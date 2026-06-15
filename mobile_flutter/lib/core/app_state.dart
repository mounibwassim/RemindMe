import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';
import 'notification_service.dart';
import '../models/task.dart';
import '../models/analytics_summary.dart';
import '../models/audit_log.dart';

class AppState extends ChangeNotifier {
  AppState({ThemeMode initialTheme = ThemeMode.system}) {
    themeMode = initialTheme;
    _loadSession();
    _startForegroundScheduler();
  }

  // ── Configuration ────────────────────────────────────────────────────────
  static String get _defaultBaseUrl {
    const explicitUrl = String.fromEnvironment('API_URL');
    if (explicitUrl.isNotEmpty) {
      return explicitUrl;
    }
    return 'https://remindme-backend-k9mb.onrender.com';
  }

  final ApiClient api = ApiClient(baseUrl: _defaultBaseUrl);
  final NotificationService _notifications = NotificationService();

  // ── Session State ─────────────────────────────────────────────────────────
  String? session;
  String? firebaseUid;
  String? displayName;
  String? email;
  String? username;
  String? avatarEmoji;

  bool isLoading = false;
  String? errorMessage;
  String? successMessage;

  // ── Production Resiliency States ──────────────────────────────────────────
  bool isOffline = false;
  bool isReconnecting = false;
  bool isWarmingUp = false;
  bool _hasDoneInitialWarmup = false;
  List<Map<String, dynamic>> _offlineMutationQueue = [];
  final Set<String> _loggedMissedTasks = {};
  final Set<String> _loggedScheduledTasks = {};
  final Set<String> _foregroundTriggeredTasks = {};

  bool get isSignedIn => session != null;
  bool get isFirebaseUser => firebaseUid != null;
  bool get isEncryptionActive => session != null;

  // ── App Data (Single Source of Truth with Cache Support) ──────────────────
  List<TaskItem> tasks = [];
  AnalyticsSummary? analytics;
  List<AuditLog> auditLogs = [];

  // ── Settings ──────────────────────────────────────────────────────────────
  ThemeMode themeMode = ThemeMode.light;
  bool notificationsEnabled = true;
  bool encryptionVisible = false;
  String auditPeriod = "week"; // "week" or "month"

  final StreamController<TaskItem> _triggeredTaskController =
      StreamController<TaskItem>.broadcast();
  Stream<TaskItem> get onTaskTriggered => _triggeredTaskController.stream;

  bool get isNotificationPermissionGranted =>
      _notifications.isPermissionGranted;

  String get encryptionMethod => 'AES-256-GCM';
  String get keyDerivation => 'PBKDF2-HMAC-SHA256';

  // ── Initialization & Caching ──────────────────────────────────────────────

  Future<void> _loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    session = prefs.getString('session_id');
    firebaseUid = prefs.getString('user_uid');
    displayName = prefs.getString('display_name');
    email = prefs.getString('email');
    username = prefs.getString('username');
    avatarEmoji = prefs.getString('avatar_emoji');

    final themeStr = prefs.getString('theme_mode') ?? 'light';
    themeMode = ThemeMode.values.firstWhere(
      (m) => m.name == themeStr,
      orElse: () => ThemeMode.light,
    );

    // Initial load from local cache to prevent blank screens
    await _loadLocalCache();
    notifyListeners();

    // Trigger dynamic backend environment probing and warmup health check immediately on launch
    await performWarmupCheck();

    // Initialize notifications once on launch (asks only once)
    await initNotifications();

    if (session != null) {
      api.setSession(session!);
      await refreshAll();
    }
    notifyListeners();
  }

  Future<void> initNotifications() async {
    final prefs = await SharedPreferences.getInstance();
    await _notifications.init();

    final requestedBefore =
        prefs.getBool('has_requested_notifications') ?? false;
    if (!requestedBefore) {
      debugPrint(
          'AppState: Triggering first-time notification permission request...');
      await _notifications.requestPermissions();
      await prefs.setBool('has_requested_notifications', true);
    } else {
      debugPrint(
          'AppState: Notifications already requested before, checking current status...');
      await _notifications.checkPermissions();
    }
  }

  Future<void> requestNotificationPermissions() async {
    await _notifications.requestPermissions();
    notifyListeners();
  }

  Future<void> sendTestNotification() async {
    await _notifications.sendTestNotification();
  }

  Future<void> sendTestScheduledNotification() async {
    await _notifications.sendTestScheduledNotification();
  }

  Future<void> _saveSession() async {
    final prefs = await SharedPreferences.getInstance();
    if (session != null) {
      await prefs.setString('session_id', session!);
      await prefs.setString('user_uid', firebaseUid ?? '');
      await prefs.setString('display_name', displayName ?? '');
      await prefs.setString('email', email ?? '');
      await prefs.setString('username', username ?? '');
      await prefs.setString('avatar_emoji', avatarEmoji ?? '');
    } else {
      await prefs.remove('session_id');
      await prefs.remove('user_uid');
      await prefs.remove('display_name');
      await prefs.remove('email');
      await prefs.remove('username');
      await prefs.remove('avatar_emoji');

      // Clean up cache on logout
      await prefs.remove('cached_tasks');
      await prefs.remove('cached_analytics');
      await prefs.remove('cached_audit_logs');
      await prefs.remove('offline_mutation_queue');
    }
  }

  Future<void> _saveThemePreference() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('theme_mode', themeMode.name);
  }

  // ── Local Caching Implementation ──────────────────────────────────────────

  Future<void> _loadLocalCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      final tasksStr = prefs.getString('cached_tasks');
      if (tasksStr != null) {
        final List<dynamic> decoded = jsonDecode(tasksStr);
        tasks =
            _sortTasks(decoded.map((json) => TaskItem.fromJson(json)).toList());
      }

      final analyticsStr = prefs.getString('cached_analytics');
      if (analyticsStr != null) {
        analytics = AnalyticsSummary.fromJson(jsonDecode(analyticsStr));
      }

      final auditStr = prefs.getString('cached_audit_logs');
      if (auditStr != null) {
        final List<dynamic> decoded = jsonDecode(auditStr);
        auditLogs = decoded.map((json) => AuditLog.fromJson(json)).toList();
      }

      final queueStr = prefs.getString('offline_mutation_queue');
      if (queueStr != null) {
        _offlineMutationQueue =
            List<Map<String, dynamic>>.from(jsonDecode(queueStr));
      }

      notifyListeners();
    } catch (e) {
      debugPrint('AppState: Failed to load local cache: $e');
    }
  }

  Future<void> _saveLocalCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(
          'cached_tasks', jsonEncode(tasks.map((t) => t.toJson()).toList()));
      if (analytics != null) {
        await prefs.setString(
            'cached_analytics', jsonEncode(analytics!.toJson()));
      }
      await prefs.setString('cached_audit_logs',
          jsonEncode(auditLogs.map((a) => a.toJson()).toList()));
      await prefs.setString(
          'offline_mutation_queue', jsonEncode(_offlineMutationQueue));
    } catch (e) {
      debugPrint('AppState: Failed to save local cache: $e');
    }
  }

  // ── Warm-up Sequencer for Render Free Tier Cold Starts ────────────────────

  Future<void> performWarmupCheck() async {
    final showWarmup = !_hasDoneInitialWarmup;
    if (showWarmup) {
      isWarmingUp = true;
      notifyListeners();
    }

    final prefs = await SharedPreferences.getInstance();
    String? customUrl = prefs.getString('custom_api_url');

    if (customUrl != null) {
      final normalized = customUrl.trim().toLowerCase();
      // Clear defunct or legacy custom URLs
      if (normalized == 'https://remindme.onrender.com' ||
          normalized == 'http://remindme.onrender.com' ||
          normalized == 'https://api-remindme.onrender.com' ||
          normalized == 'http://api-remindme.onrender.com' ||
          normalized == 'https://remindme-backend.onrender.com' ||
          normalized == 'http://remindme-backend.onrender.com') {
        await prefs.remove('custom_api_url');
        customUrl = null;
        debugPrint('AppState: Cleared defunct cached custom API URL.');
      }
    }

    if (customUrl != null && customUrl.isNotEmpty) {
      api.baseUrl = customUrl;
    } else {
      const explicitUrl = String.fromEnvironment('API_URL');
      api.baseUrl = explicitUrl.isNotEmpty
          ? explicitUrl
          : 'https://remindme-backend-k9mb.onrender.com';
    }

    debugPrint('AppState: Final API URL configured to: ${api.baseUrl}');

    final stopwatch = Stopwatch()..start();
    try {
      debugPrint(
          'AppState: Pinging active backend at ${api.baseUrl}/health ...');
      final response = await http
          .get(Uri.parse('${api.baseUrl}/health'))
          .timeout(const Duration(seconds: 15)); // Strict 15s timeout
      stopwatch.stop();
      if (response.statusCode == 200) {
        isWarmingUp = false;
        isOffline = false;
        _hasDoneInitialWarmup = true;
        notifyListeners();
        debugPrint(
            'AppState: Backend connection verified. Processing offline mutations.');
        await _processOfflineQueue();
      } else {
        throw Exception(
            'Server health check returned status code: ${response.statusCode}');
      }
    } catch (e) {
      stopwatch.stop();
      debugPrint(
          'AppState: Active backend connection failed after ${stopwatch.elapsedMilliseconds}ms. Error: $e');
      if (showWarmup) {
        _backgroundWarmup();
      } else {
        isOffline = true;
        _hasDoneInitialWarmup = true;
        notifyListeners();
      }
    }
  }

  Future<void> _backgroundWarmup() async {
    int attempts = 0;
    while (attempts < 10 && isWarmingUp) {
      try {
        debugPrint(
            'AppState: Background warmup attempt ${attempts + 1}/10 at ${api.baseUrl}...');
        final response = await http
            .get(Uri.parse('${api.baseUrl}/health'))
            .timeout(const Duration(
                seconds: 15)); // Keep 15s timeout for warmup checks
        if (response.statusCode == 200) {
          isWarmingUp = false;
          isOffline = false;
          _hasDoneInitialWarmup = true;
          debugPrint('AppState: Server woke up! Syncing cached state.');
          notifyListeners();
          await _processOfflineQueue();
          await refreshAll();
          break;
        }
      } catch (_) {
        attempts++;
        await Future.delayed(const Duration(seconds: 5));
      }
    }

    if (isWarmingUp) {
      isWarmingUp = false;
      isOffline = true;
      _hasDoneInitialWarmup = true;
      notifyListeners();
    }
  }

  // ── Offline Mutations Queue ────────────────────────────────────────────────

  Future<void> _addToOfflineQueue(
      String action, Map<String, dynamic> data) async {
    _offlineMutationQueue.add({
      'action': action,
      'data': data,
      'timestamp': DateTime.now().toIso8601String(),
    });
    await _saveLocalCache();
    isOffline = true;
    notifyListeners();
  }

  Future<void> _processOfflineQueue() async {
    if (_offlineMutationQueue.isEmpty) return;

    isReconnecting = true;
    notifyListeners();

    final queueCopy = List<Map<String, dynamic>>.from(_offlineMutationQueue);
    _offlineMutationQueue.clear();
    await _saveLocalCache();

    try {
      for (final item in queueCopy) {
        final action = item['action'];
        final data = item['data'];

        if (action == 'create') {
          await api.createTask(TaskDraft(
            title: data['title'],
            dueIso: data['due_iso'],
            priority: data['priority'],
            category: data['category'],
            sound: data['sound'] ?? 'Default',
            description: data['description'] ?? '',
          ));
        } else if (action == 'update') {
          await api.updateTask(
              data['id'],
              TaskDraft(
                title: data['title'],
                dueIso: data['due_iso'],
                priority: data['priority'],
                category: data['category'],
                sound: data['sound'] ?? 'Default',
                description: data['description'] ?? '',
              ));
        } else if (action == 'complete') {
          await api.completeTask(data['id']);
        } else if (action == 'reopen') {
          await api.reopenTask(data['id']);
        } else if (action == 'delete') {
          await api.deleteTask(data['id']);
        } else if (action == 'snooze') {
          await api.snoozeTask(data['id'], data['minutes']);
        }
      }
      isOffline = false;
      isReconnecting = false;
      notifyListeners();
      await _reloadData();
    } catch (e) {
      debugPrint(
          'AppState: Failed to process offline queue, returning items to queue: $e');
      _offlineMutationQueue.insertAll(0, queueCopy);
      await _saveLocalCache();
      isReconnecting = false;
      notifyListeners();
    }
  }

  // ── Authentication ────────────────────────────────────────────────────────

  Future<void> login(String emailInput, String password) async {
    await _guard(() async {
      try {
        final res = await api.login(emailInput, password);
        session = res['session_id'];
        firebaseUid = res['uid'] ?? res['user_uid'];
        displayName = res['display_name'];
        email = res['email'];
        username = res['username'];
        avatarEmoji = res['avatar_emoji'];
        api.setSession(session!);
        await _saveSession();
        await refreshAll();
      } catch (e) {
        if (e is ApiException) {
          throw ApiException('Login failed: ${e.message}');
        }
        throw ApiException('Login failed');
      }
    });
  }

  Future<void> devLogin(
      String usernameInput, String emailInput, String secret) async {
    await _guard(() async {
      try {
        final res = await api.devLogin(usernameInput, emailInput, secret);
        session = res['session_id'];
        username = res['username'];
        email = res['email'];
        firebaseUid = null;
        displayName = res['username'];
        api.setSession(session!);
        await _saveSession();
        await refreshAll();
      } catch (e) {
        throw ApiException('Login failed');
      }
    });
  }

  Future<void> firebaseSignIn(String email, String password) =>
      login(email, password);

  Future<void> createAccount(
      String emailInput, String password, String name) async {
    await _guard(() async {
      final res = await api.register(emailInput, password, name);
      session = res['session_id'];
      firebaseUid = res['uid'] ?? res['user_uid'];
      displayName = res['display_name'];
      email = res['email'];
      username = res['username'];
      avatarEmoji = res['avatar_emoji'];
      api.setSession(session!);
      await _saveSession();
      await refreshAll();
    });
  }

  Future<void> firebaseSignUp(String email, String password, String name) =>
      createAccount(email, password, name);

  Future<void> forgotPassword(String user) async {
    isLoading = true;
    errorMessage = null;
    notifyListeners();
    try {
      String result = await api.forgotPassword(user);
      successMessage = result;
      errorMessage = null;
      notifyListeners();
    } catch (e, stack) {
      debugPrint('ForgotPassword Critical Failure: $e');
      if (e is ConnectionException) {
        errorMessage =
            'Connection error. Please verify the backend server is running.';
      } else {
        final msg = e.toString();
        if (msg.contains('getaddrinfo') ||
            msg.contains('SocketException') ||
            msg.contains('Failed host lookup')) {
          errorMessage =
              'Database connection error. Please make sure the Supabase database is active/unpaused.';
        } else {
          errorMessage = msg;
        }
      }
      await api.logError('ForgotPassword error: $e\n$stack');
      notifyListeners();
      rethrow;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> confirmPasswordReset(String code, String password,
      {String? email}) async {
    isLoading = true;
    errorMessage = null;
    notifyListeners();
    try {
      await api.confirmPasswordReset(code, password, email: email);
    } catch (e) {
      rethrow;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  void clearError() {
    errorMessage = null;
    successMessage = null;
    notifyListeners();
  }

  Future<void> updateAvatar(String avatar) async {
    await _guard(() async {
      await api.updateAvatar(avatar);
      avatarEmoji = avatar;
      await _saveSession();
    });
  }

  Future<void> changePassword(
      String currentPassword, String newPassword) async {
    // For password changes we must surface backend errors to the UI so the
    // caller can decide what to do (e.g. show "current password incorrect"
    // and NOT sign the user out). Do not swallow exceptions here.
    isLoading = true;
    errorMessage = null;
    notifyListeners();
    try {
      await api.changePassword(currentPassword, newPassword);
    } catch (e) {
      // Propagate the error so callers (UI) can handle it explicitly.
      rethrow;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  // ── Task Operations (Global Synchronization with Caching & Offline Queuing)

  Future<void> refreshAll() async {
    // If reconnecting/warming up, run ping check first
    if (isOffline) {
      await performWarmupCheck();
    }
    await _guard(() async {
      await _reloadData();
    });
  }

  Future<void> _reloadData() async {
    try {
      final rawTasks = await api.getTasks();
      tasks = _sortTasks(rawTasks);
      isOffline = false;

      try {
        analytics = await api.getAnalyticsSummary(period: auditPeriod);
      } catch (e) {
        debugPrint('AppState: Analytics fetch failed: $e');
        analytics = _calculateFallbackAnalytics(tasks);
      }

      // Always enrich weekly and monthly charts using locally calculated distributions
      if (analytics != null) {
        final local = _calculateFallbackAnalytics(tasks);
        analytics = analytics!.copyWith(
          weeklyLabels: local.weeklyLabels,
          weeklyCounts: local.weeklyCounts,
          weeklyRange: local.weeklyRange,
          monthlyLabels: local.monthlyLabels,
          monthlyCounts: local.monthlyCounts,
          monthlyRange: local.monthlyRange,
        );
      }

      try {
        auditLogs = await api.getAuditLogs(limit: 1000, period: auditPeriod);
      } catch (e) {
        debugPrint('AppState: Audit logs fetch failed: $e');
        auditLogs = [];
      }

      await _saveLocalCache();
    } catch (e) {
      debugPrint('AppState: Network sync failed. Serving cached data: $e');
      isOffline = true;
      await _loadLocalCache();
    }

    await _rescheduleNotifications();
  }

  AnalyticsSummary _calculateFallbackAnalytics(List<TaskItem> list) {
    final total = list.length;
    final completed = list.where((t) => t.isCompleted).length;
    final pending =
        list.where((t) => !t.isCompleted && t.isOverdue == 1).length;
    final upcoming =
        list.where((t) => !t.isCompleted && t.isOverdue == 0).length;

    // Calculate Weekly Distribution
    final now = DateTime.now();
    // Find the most recent Monday
    final monday = now.subtract(Duration(days: now.weekday - 1));
    final mondayStart = DateTime(monday.year, monday.month, monday.day);
    final sundayEnd = mondayStart.add(const Duration(days: 7));

    final weeklyLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    final weeklyCounts = List<int>.filled(7, 0);

    // Calculate Monthly Distribution
    final currentMonthStart = DateTime(now.year, now.month, 1);
    final nextMonthStart = now.month == 12
        ? DateTime(now.year + 1, 1, 1)
        : DateTime(now.year, now.month + 1, 1);
    final lastDay = nextMonthStart.subtract(const Duration(days: 1)).day;

    final monthlyLabels = ['W1', 'W2', 'W3', 'W4'];
    final monthlyCounts = List<int>.filled(4, 0);
    if (lastDay > 28) {
      monthlyLabels.add('W5');
      monthlyCounts.add(0);
    }

    for (final task in list) {
      if (task.isCompleted &&
          task.completedIso != null &&
          task.completedIso!.isNotEmpty) {
        try {
          final compDt = DateTime.parse(task.completedIso!).toLocal();

          // Weekly check
          if (compDt.isAfter(mondayStart) && compDt.isBefore(sundayEnd)) {
            final dayIndex = compDt.weekday - 1; // Mon=0, Sun=6
            if (dayIndex >= 0 && dayIndex < 7) {
              weeklyCounts[dayIndex]++;
            }
          }

          // Monthly check
          if (compDt.year == now.year && compDt.month == now.month) {
            final day = compDt.day;
            if (day <= 7) {
              monthlyCounts[0]++;
            } else if (day <= 14) {
              monthlyCounts[1]++;
            } else if (day <= 21) {
              monthlyCounts[2]++;
            } else if (day <= 28) {
              monthlyCounts[3]++;
            } else if (monthlyCounts.length > 4) {
              monthlyCounts[4]++;
            }
          }
        } catch (e) {
          debugPrint('Error parsing completedIso: $e');
        }
      }
    }

    final monthName = _getMonthName(now.month);
    final weeklyRangeStr =
        "${mondayStart.day} ${_getMonthAbbr(mondayStart.month)} ${mondayStart.year} - ${sundayEnd.subtract(const Duration(days: 1)).day} ${_getMonthAbbr(sundayEnd.subtract(const Duration(days: 1)).month)} ${sundayEnd.year}";
    final monthlyRangeStr =
        "01 - ${lastDay.toString().padLeft(2, '0')} $monthName ${now.year}";

    return AnalyticsSummary(
      totalTasks: total,
      completed: completed,
      pending: pending,
      upcoming: upcoming,
      weeklyLabels: weeklyLabels,
      weeklyCounts: weeklyCounts,
      weeklyRange: weeklyRangeStr,
      monthlyLabels: monthlyLabels,
      monthlyCounts: monthlyCounts,
      monthlyRange: monthlyRangeStr,
      audit: {},
      aiInsight: isOffline
          ? 'Offline Mode active. Syncing later.'
          : 'Syncing with backend...',
    );
  }

  String _getMonthName(int month) {
    const names = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December'
    ];
    return names[month - 1];
  }

  String _getMonthAbbr(int month) {
    const names = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec'
    ];
    return names[month - 1];
  }

  Future<void> createTask(TaskDraft draft) async {
    await _guard(() async {
      if (isOffline) {
        final tempId = 'temp_${DateTime.now().millisecondsSinceEpoch}';
        final tempTask = TaskItem(
          id: tempId,
          title: draft.title,
          dueIso: draft.dueIso,
          priority: draft.priority,
          notified: 0,
          category: draft.category,
          sound: draft.sound,
          description: draft.description,
          isOverdue: 0,
          createdIso: DateTime.now().toIso8601String(),
        );
        tasks.insert(0, tempTask);
        tasks = _sortTasks(tasks);
        await _saveLocalCache();

        await _addToOfflineQueue('create', {
          'title': draft.title,
          'due_iso': draft.dueIso,
          'priority': draft.priority,
          'category': draft.category,
          'sound': draft.sound,
          'description': draft.description,
        });
        // Schedule notification locally for the newly created offline task
        try {
          await _scheduleNotificationForTask(tempTask);
        } catch (e) {
          debugPrint(
              'AppState: Failed to schedule notification for temp task: $e');
        }
      } else {
        final created = await api.createTask(draft);
        // Schedule notification for the created task immediately
        try {
          await _scheduleNotificationForTask(created);
        } catch (e) {
          debugPrint(
              'AppState: Failed to schedule notification for created task: $e');
        }
        await _reloadData();
      }
    });
  }

  Future<void> updateTask(String id, TaskDraft draft) async {
    await _guard(() async {
      _loggedMissedTasks.remove(id);
      _loggedScheduledTasks.remove(id);
      _foregroundTriggeredTasks.remove(id);
      if (isOffline) {
        final idx = tasks.indexWhere((t) => t.id == id);
        if (idx != -1) {
          tasks[idx] = TaskItem(
            id: id,
            title: draft.title,
            dueIso: draft.dueIso,
            priority: draft.priority,
            notified: 0,
            category: draft.category,
            sound: draft.sound,
            description: draft.description,
            isOverdue: 0,
            createdIso: tasks[idx].createdIso,
          );
          tasks = _sortTasks(tasks);
          await _saveLocalCache();
        }
        await _addToOfflineQueue('update', {
          'id': id,
          'title': draft.title,
          'due_iso': draft.dueIso,
          'priority': draft.priority,
          'category': draft.category,
          'sound': draft.sound,
          'description': draft.description,
        });
        // Reschedule notification for updated task in offline mode
        try {
          final idx = tasks.indexWhere((t) => t.id == id);
          if (idx != -1) await _scheduleNotificationForTask(tasks[idx]);
        } catch (e) {
          debugPrint(
              'AppState: Failed to reschedule notification for updated task: $e');
        }
      } else {
        final updated = await api.updateTask(id, draft);
        try {
          await _scheduleNotificationForTask(updated);
        } catch (e) {
          debugPrint(
              'AppState: Failed to reschedule notification for updated task (online): $e');
        }
        await _reloadData();
      }
    });
  }

  Future<void> completeTask(TaskItem task) async {
    await _guard(() async {
      await _notifications.cancelNotification(task.id);
      if (isOffline) {
        final idx = tasks.indexWhere((t) => t.id == task.id);
        if (idx != -1) {
          tasks[idx] = TaskItem(
            id: task.id,
            title: task.title,
            dueIso: task.dueIso,
            priority: task.priority,
            notified: task.notified,
            category: task.category,
            sound: task.sound,
            description: task.description,
            isOverdue: 0,
            createdIso: task.createdIso,
            status: 'completed',
            completedIso: DateTime.now().toIso8601String(),
          );
          tasks = _sortTasks(tasks);
          await _saveLocalCache();
        }
        await _addToOfflineQueue('complete', {'id': task.id});
      } else {
        await api.completeTask(task.id);
        await _reloadData();
      }
    });
  }

  Future<void> toggleTask(TaskItem task) async {
    await _guard(() async {
      _loggedMissedTasks.remove(task.id);
      _loggedScheduledTasks.remove(task.id);
      if (!task.isCompleted) {
        await _notifications.cancelNotification(task.id);
      }
      if (isOffline) {
        final isComp = task.isCompleted;
        final idx = tasks.indexWhere((t) => t.id == task.id);
        if (idx != -1) {
          tasks[idx] = TaskItem(
            id: task.id,
            title: task.title,
            dueIso: task.dueIso,
            priority: task.priority,
            notified: task.notified,
            category: task.category,
            sound: task.sound,
            description: task.description,
            isOverdue: 0,
            createdIso: task.createdIso,
            status: isComp ? 'open' : 'completed',
            completedIso: isComp ? null : DateTime.now().toIso8601String(),
          );
          tasks = _sortTasks(tasks);
          await _saveLocalCache();
        }
        await _addToOfflineQueue(
            isComp ? 'reopen' : 'complete', {'id': task.id});
      } else {
        if (task.isCompleted) {
          await api.reopenTask(task.id);
        } else {
          await api.completeTask(task.id);
        }
        await _reloadData();
      }
    });
  }

  Future<void> snoozeTask(TaskItem task, int minutes) async {
    await _guard(() async {
      _loggedMissedTasks.remove(task.id);
      _loggedScheduledTasks.remove(task.id);
      _foregroundTriggeredTasks.remove(task.id);
      if (isOffline) {
        final idx = tasks.indexWhere((t) => t.id == task.id);
        if (idx != -1) {
          final newDue = DateTime.now().add(Duration(minutes: minutes));
          tasks[idx] = TaskItem(
            id: task.id,
            title: task.title,
            dueIso: newDue.toIso8601String(),
            priority: task.priority,
            notified: 0,
            category: task.category,
            sound: task.sound,
            description: task.description,
            isOverdue: 0,
            createdIso: task.createdIso,
            status: 'snoozed',
            notificationStatus: 'snoozed',
          );
          tasks = _sortTasks(tasks);
          await _saveLocalCache();
        }
        await _addToOfflineQueue('snooze', {'id': task.id, 'minutes': minutes});
        // Reschedule local notification for snoozed task
        try {
          final idx = tasks.indexWhere((t) => t.id == task.id);
          if (idx != -1) await _scheduleNotificationForTask(tasks[idx]);
        } catch (e) {
          debugPrint(
              'AppState: Failed to reschedule notification for snoozed task: $e');
        }
      } else {
        await api.snoozeTask(task.id, minutes);
        await _reloadData();
      }
    });
  }

  Future<void> deleteTask(TaskItem task) async {
    await _guard(() async {
      await _notifications.cancelNotification(task.id);
      if (isOffline) {
        tasks.removeWhere((t) => t.id == task.id);
        await _saveLocalCache();
        await _addToOfflineQueue('delete', {'id': task.id});
      } else {
        await api.deleteTask(task.id);
        await _reloadData();
      }
    });
  }

  Future<void> clearCompletedHistory() async {
    await _guard(() async {
      final completed = tasks.where((t) => t.isCompleted).toList();
      for (final t in completed) {
        try {
          if (!isOffline) {
            await api.deleteTask(t.id);
          }
        } catch (e) {
          debugPrint('AppState: Failed to delete completed task ${t.id}: $e');
        }
      }

      try {
        if (!isOffline) {
          await api.clearAuditLogs();
        }
      } catch (e) {
        debugPrint('AppState: Failed to clear audit logs: $e');
      }
      auditLogs = [];

      try {
        if (!isOffline) {
          await api.resetAnalytics();
        }
      } catch (e) {
        debugPrint('AppState: Failed to reset analytics: $e');
      }
      analytics = _calculateFallbackAnalytics([]);

      try {
        await _notifications.cancelAll();
      } catch (e) {
        debugPrint('AppState: Failed to cancel notifications: $e');
      }

      try {
        await _reloadData();
      } catch (e) {
        debugPrint('AppState: full reload failed after clear: $e');
        await _reloadTasksOnly();
      }
    });
  }

  Future<void> _reloadTasksOnly() async {
    try {
      final rawTasks = await api.getTasks();
      tasks = _sortTasks(rawTasks);
      isOffline = false;
      await _saveLocalCache();
    } catch (_) {
      isOffline = true;
      await _loadLocalCache();
    }

    try {
      await _rescheduleNotifications();
    } catch (e) {
      debugPrint('AppState: _reloadTasksOnly reschedule failed: $e');
    }
    notifyListeners();
  }

  Future<void> clearAllHistory() async {
    await _guard(() async {
      if (!isOffline) {
        await api.clearAllTasks();
      }
      tasks = [];
      analytics = null;
      auditLogs = [];
      await _saveLocalCache();
      await _notifications.cancelAll();
      await _reloadData();
    });
  }

  Future<void> deleteAuditLog(String logId) async {
    await _guard(() async {
      if (!isOffline) {
        await api.deleteAuditLog(logId);
      }
      auditLogs.removeWhere((l) => l.id == logId);
      await _saveLocalCache();
      await _reloadData();
    });
  }

  Future<void> clearAuditLogs() async {
    await _guard(() async {
      if (!isOffline) {
        await api.clearAuditLogs();
      }
      auditLogs = [];
      await _saveLocalCache();
      await _reloadData();
    });
  }

  List<TaskItem> _sortTasks(List<TaskItem> list) {
    final pending = list.where((t) => !t.isCompleted).toList()
      ..sort((a, b) => a.dueAt.compareTo(b.dueAt));
    final completed = list.where((t) => t.isCompleted).toList()
      ..sort((a, b) =>
          b.completedAt?.compareTo(a.completedAt ?? DateTime(0)) ?? 0);
    return [...pending, ...completed];
  }

  Future<void> _rescheduleNotifications() async {
    if (!notificationsEnabled) return;
    await _notifications.init();
    // Do NOT cancelAll() here to prevent race conditions that cancel notifications
    // immediately as they are triggered in the foreground.

    final now = DateTime.now();
    for (final task in tasks.where((t) => !t.isCompleted)) {
      if (task.dueAt.isAfter(now)) {
        if (task.notificationStatus == 'pending' &&
            !_loggedScheduledTasks.contains(task.id)) {
          try {
            if (!isOffline) {
              _loggedScheduledTasks.add(task.id);
              await api.logNotificationEvent(
                task.id,
                'notification_scheduled',
                extra: 'Task: ${task.title}',
              );
            }
          } catch (e) {
            _loggedScheduledTasks.remove(task.id);
            debugPrint(
                'AppState: Failed to log notification_scheduled for task ${task.id}: $e');
          }
        }

        // Ensure previous scheduled notification for this task is removed
        try {
          await _notifications.cancelNotification(task.id);
        } catch (_) {}

        await _notifications.scheduleNotification(
          id: task.id,
          title: task.title,
          body: 'Alarm: ${task.title} is due now!',
          scheduledDate: task.dueAt,
          onTriggered: () {
            // Handled exclusively by the foreground scheduler
            debugPrint(
                '[Notification] Web timer fired for task: ${task.title}');
          },
        );
      }
    }
  }

  Future<void> _scheduleNotificationForTask(TaskItem task) async {
    if (!notificationsEnabled) return;
    try {
      // Ensure plugin initialized and permission requested when needed
      await _notifications.init();
      if (!_notifications.isPermissionGranted) {
        await _notifications.requestPermissions();
      }
    } catch (e) {
      debugPrint('AppState: Notification init/permission check failed: $e');
    }

    // Cancel any existing scheduled notification for this task first
    try {
      await _notifications.cancelNotification(task.id);
    } catch (e) {
      debugPrint(
          'AppState: Failed to cancel existing notification for ${task.id}: $e');
    }

    if (task.isCompleted) return;

    final now = DateTime.now();
    // If due time is in the past but recent, show immediately; otherwise skip
    if (task.dueAt.isBefore(now)) {
      final recentThreshold = now.subtract(const Duration(minutes: 5));
      if (task.dueAt.isAfter(recentThreshold)) {
        await _notifications.showNotification(
          id: task.id,
          title: task.title,
          body: 'Reminder: ${task.title}',
          payload: 'task:${task.id}',
        );
        return;
      }
      return;
    }

    try {
      await _notifications.scheduleNotification(
        id: task.id,
        title: task.title,
        body: 'Reminder: ${task.title}',
        scheduledDate: task.dueAt,
        onTriggered: () {
          debugPrint('[Notification] Scheduled fired for task: ${task.title}');
        },
      );
    } catch (e) {
      debugPrint(
          'AppState: Failed to schedule notification for ${task.id}: $e');
    }
  }

  Future<void> logNotificationEvent(String taskId, String event,
      {String extra = ''}) async {
    await _guard(() async {
      if (!isOffline) {
        await api.logNotificationEvent(taskId, event, extra: extra);
      }
      await _reloadData();
    });
  }

  // ── Settings ──────────────────────────────────────────────────────────────

  void toggleThemeMode() {
    if (themeMode == ThemeMode.system) {
      final brightness =
          WidgetsBinding.instance.platformDispatcher.platformBrightness;
      themeMode =
          brightness == Brightness.dark ? ThemeMode.light : ThemeMode.dark;
    } else {
      themeMode =
          themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    }
    _saveThemePreference();
    notifyListeners();
  }

  void setThemeMode(ThemeMode mode) {
    themeMode = mode;
    _saveThemePreference();
    notifyListeners();
  }

  void setAuditPeriod(String period) {
    auditPeriod = period;
    refreshAll();
  }

  void toggleEncryptionVisibility() {
    encryptionVisible = !encryptionVisible;
    notifyListeners();
  }

  void toggleNotifications() {
    notificationsEnabled = !notificationsEnabled;
    if (notificationsEnabled) {
      _rescheduleNotifications();
    } else {
      _notifications.cancelAll();
    }
    notifyListeners();
  }

  Future<void> changeApiBaseUrl(String newUrl) async {
    final prefs = await SharedPreferences.getInstance();
    final url = newUrl.trim();
    if (url.isEmpty || url == 'https://remindme-backend-k9mb.onrender.com') {
      await prefs.remove('custom_api_url');
    } else {
      await prefs.setString('custom_api_url', url);
    }
    await performWarmupCheck();
    notifyListeners();
  }

  // ── Reset/Sign Out ────────────────────────────────────────────────────────

  Future<void> resetAnalytics() async {
    await _guard(() async {
      if (!isOffline) {
        await api.resetAnalytics();
      }
      analytics = _calculateFallbackAnalytics([]);
      await _reloadData();
    });
  }

  void signOut() {
    session = null;
    firebaseUid = null;
    displayName = null;
    email = null;
    username = null;
    tasks = [];
    analytics = null;
    auditLogs = [];
    errorMessage = null;
    _hasDoneInitialWarmup = false;
    _loggedMissedTasks.clear();
    _loggedScheduledTasks.clear();
    _foregroundTriggeredTasks.clear();
    _saveSession();
    notifyListeners();
  }

  Future<void> resetAssistantState() async {
    await _guard(() async {
      if (!isOffline) {
        await api.resetAssistantState();
      }
    });
  }

  // ── Internal ──────────────────────────────────────────────────────────────

  Future<T?> _guard<T>(Future<T> Function() action) async {
    isLoading = true;
    errorMessage = null;
    notifyListeners();
    try {
      return await action();
    } catch (e, stack) {
      debugPrint('AppState Error: $e\n$stack');
      if (e is ConnectionException) {
        errorMessage =
            'Connection error. Please verify the backend server is running.';
      } else {
        final msg = e.toString();
        if (msg.contains('getaddrinfo') ||
            msg.contains('SocketException') ||
            msg.contains('Failed host lookup')) {
          errorMessage =
              'Database connection error. Please make sure the Supabase database is active/unpaused.';
        } else {
          errorMessage = msg;
        }
      }
      try {
        if (!isOffline) {
          await api.logError('Frontend Error: $e\nStack: $stack');
        }
      } catch (_) {}
      notifyListeners();
      return null;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Timer? _foregroundSchedulerTimer;

  void _startForegroundScheduler() {
    if (_foregroundSchedulerTimer != null) return;
    _foregroundSchedulerTimer =
        Timer.periodic(const Duration(seconds: 4), (timer) async {
      if (!isSignedIn) return;
      final now = DateTime.now();
      bool statusChanged = false;

      for (int i = 0; i < tasks.length; i++) {
        final task = tasks[i];
        if (!task.isCompleted &&
            task.dueAt.isBefore(now) &&
            task.dueAt.isAfter(now.subtract(const Duration(seconds: 90))) &&
            task.notificationStatus == 'pending' &&
            !_foregroundTriggeredTasks.contains(task.id)) {
          _foregroundTriggeredTasks.add(task.id);
          debugPrint('[Foreground Scheduler] Triggering task: ${task.title}');

          // 1. Trigger in-app popup dialog via the stream
          _triggeredTaskController.add(task);

          // 3. Mark locally as triggered to avoid double fires
          tasks[i] = TaskItem(
            id: task.id,
            title: task.title,
            dueIso: task.dueIso,
            priority: task.priority,
            notified: 1,
            category: task.category,
            sound: task.sound,
            description: task.description,
            isOverdue: task.isOverdue,
            createdIso: task.createdIso,
            status: task.status,
            completedIso: task.completedIso,
            notificationStatus: 'triggered',
          );
          statusChanged = true;

          // 4. Log to backend
          if (!isOffline) {
            try {
              await api.logNotificationEvent(task.id, 'notification_triggered');
              // Automatically reload data to fetch latest tasks status
              _reloadData();
            } catch (e) {
              debugPrint('[Foreground Scheduler] Failed to log event: $e');
            }
          }
        }
      }

      if (statusChanged) {
        notifyListeners();
      }
    });
  }

  @override
  void dispose() {
    _foregroundSchedulerTimer?.cancel();
    _triggeredTaskController.close();
    super.dispose();
  }
}
