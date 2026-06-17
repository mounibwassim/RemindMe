import 'dart:ui';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;
import 'web_notifier_stub.dart' if (dart.library.js) 'web_notifier_web.dart'
    as web_notifier;
import '../main.dart';

typedef NotificationTapHandler = void Function(String? payload);

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  static const String taskChannelId = 'remindme_task_alarms_v3';
  static const String taskChannelName = 'Task alarms';
  static const String taskChannelDescription =
      'Exact RemindMe alerts for task deadlines';

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  /// Guard: only initialize plugin once.
  bool _initialized = false;

  static const MethodChannel _channel = MethodChannel('com.example.remindme/settings');

  Future<void> openNotificationSettings() async {
    if (kIsWeb) return;
    try {
      await _channel.invokeMethod('openNotificationSettings');
    } catch (e) {
      debugPrint('Failed to open settings: $e');
    }
  }

  static final Int64List _vibrationPattern =
      Int64List.fromList([0, 700, 250, 700, 250, 1000]);

  static final AndroidNotificationDetails _androidAlarmDetails =
      AndroidNotificationDetails(
    taskChannelId,
    taskChannelName,
    channelDescription: taskChannelDescription,
    importance: Importance.max,
    priority: Priority.max,
    category: AndroidNotificationCategory.alarm,
    visibility: NotificationVisibility.public,
    fullScreenIntent: true,
    playSound: true,
    enableVibration: true,
    vibrationPattern: _vibrationPattern,
    enableLights: true,
    ledColor: const Color(0xFF2563EB),
    ledOnMs: 1000,
    ledOffMs: 500,
    showWhen: true,
    autoCancel: true,
    ticker: 'RemindMe task alert',
    // NOTE: launcher_icon is set by flutter_launcher_icons.yaml
    largeIcon: const DrawableResourceAndroidBitmap('@mipmap/launcher_icon'),
    actions: <AndroidNotificationAction>[
      const AndroidNotificationAction(
        'snooze',
        'Snooze (15m)',
        showsUserInterface: true,
      ),
      const AndroidNotificationAction(
        'complete',
        'Complete',
        showsUserInterface: true,
      ),
    ],
  );

  Future<void> init({NotificationTapHandler? onTap}) async {
    if (kIsWeb) {
      await checkPermissions();
      return;
    }

    // Initialize timezone database once
    tzdata.initializeTimeZones();
    // Always use UTC for scheduling — avoids all device-timezone mismatches.
    // We schedule using absolute UTC instants, so tz.UTC is always correct.
    tz.setLocalLocation(tz.UTC);

    // Only initialize the plugin once to avoid clearing the tap handler
    if (!_initialized) {
      // Use launcher_icon — the name set by flutter_launcher_icons.yaml
      const androidInit =
          AndroidInitializationSettings('@mipmap/launcher_icon');
      const initSettings = InitializationSettings(android: androidInit);

      await _plugin.initialize(
        initSettings,
        onDidReceiveNotificationResponse: (details) {
          debugPrint('[Notification] Tapped: payload=${details.payload}');
          onTap?.call(details.payload);
        },
        onDidReceiveBackgroundNotificationResponse: notificationTapBackground,
      );

      final androidPlugin = _plugin.resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>();

      await androidPlugin?.createNotificationChannel(
        AndroidNotificationChannel(
          taskChannelId,
          taskChannelName,
          description: taskChannelDescription,
          importance: Importance.max,
          playSound: true,
          enableVibration: true,
          vibrationPattern: _vibrationPattern,
          ledColor: const Color(0xFF2563EB),
          enableLights: true,
        ),
      );

      _initialized = true;
      debugPrint('[Notification] Plugin initialized successfully.');
    }

    await checkPermissions();
  }

  bool _isPermissionGranted = false;
  bool get isPermissionGranted => _isPermissionGranted;

  Future<void> checkPermissions() async {
    if (kIsWeb) {
      _isPermissionGranted = web_notifier.checkWebNotificationPermission();
      return;
    }

    final androidPlugin = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    if (androidPlugin != null) {
      _isPermissionGranted =
          await androidPlugin.areNotificationsEnabled() ?? false;
      debugPrint('[Notification] areNotificationsEnabled: $_isPermissionGranted');
    }
  }

  Future<void> requestPermissions() async {
    if (kIsWeb) {
      web_notifier.requestWebNotificationPermission((granted) {
        _isPermissionGranted = granted;
      });
      return;
    }

    final androidPlugin = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    if (androidPlugin != null) {
      final currentlyEnabled = await androidPlugin.areNotificationsEnabled() ?? false;
      final granted = await androidPlugin.requestNotificationsPermission();
      
      _isPermissionGranted = granted ?? false;
      debugPrint('[Notification] Permission granted: $_isPermissionGranted');
      
      if (!currentlyEnabled && granted != true) {
        // Permission was denied or not granted, and notifications are disabled.
        // Open system notification settings for this application.
        await openNotificationSettings();
      }
      
      // Request exact alarm permission (opens system settings on Android 12+)
      await androidPlugin.requestExactAlarmsPermission();
    }
  }

  Future<void> scheduleNotification({
    required String id,
    required String title,
    required String body,
    required DateTime scheduledDate,
    VoidCallback? onTriggered,
  }) async {
    if (kIsWeb) {
      web_notifier.scheduleWebNotification(
        id: id,
        title: title,
        body: body,
        scheduledDate: scheduledDate,
        onTriggered: onTriggered ?? () {},
      );
      return;
    }

    // Ensure plugin is initialized before scheduling
    if (!_initialized) {
      await init();
    }

    final intId = id.hashCode & 0x7FFFFFFF;

    // Convert scheduledDate to UTC to avoid all timezone confusion
    final scheduledUtc = scheduledDate.toUtc();

    if (scheduledUtc.isBefore(DateTime.now().toUtc())) {
      debugPrint('[Notification] Skipped past task: $title at $scheduledUtc');
      return;
    }

    try {
      // Schedule using UTC timezone — no device timezone conversion needed
      final tzScheduled = tz.TZDateTime.from(scheduledUtc, tz.UTC);

      try {
        await _plugin.zonedSchedule(
          intId,
          title,
          body,
          tzScheduled,
          NotificationDetails(android: _androidAlarmDetails),
          androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
          uiLocalNotificationDateInterpretation:
              UILocalNotificationDateInterpretation.absoluteTime,
          payload: 'task:$id',
        );
        debugPrint('[Notification] Scheduled (exact): "$title" at $tzScheduled UTC (ID: $intId)');
      } catch (e) {
        debugPrint('[Notification] Exact scheduling failed, trying non-exact fallback: $e');
        await _plugin.zonedSchedule(
          intId,
          title,
          body,
          tzScheduled,
          NotificationDetails(android: _androidAlarmDetails),
          androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
          uiLocalNotificationDateInterpretation:
              UILocalNotificationDateInterpretation.absoluteTime,
          payload: 'task:$id',
        );
        debugPrint('[Notification] Scheduled (fallback): "$title" at $tzScheduled UTC (ID: $intId)');
      }
    } catch (e) {
      debugPrint('[Notification] Scheduling failed for "$title": $e');
    }
  }

  /// Fire an immediate notification.
  Future<void> showNotification({
    required String id,
    required String title,
    required String body,
    String? payload,
  }) async {
    if (kIsWeb) {
      web_notifier.showWebNotification(title, body);
      return;
    }

    if (!_initialized) await init();

    final intId = id.hashCode & 0x7FFFFFFF;
    await _plugin.show(
      intId,
      title,
      body,
      NotificationDetails(android: _androidAlarmDetails),
      payload: payload,
    );
    debugPrint('[Notification] Instant notification shown (ID: $intId).');
  }

  /// Fire an immediate test notification (shows instantly, no scheduling).
  Future<void> sendTestNotification() async {
    if (kIsWeb) {
      web_notifier.sendWebTestNotification();
      return;
    }

    if (!_initialized) await init();

    await _plugin.show(
      900001,
      '🔔 RemindMe Test',
      'Notifications are working! Tasks will alert you when due.',
      NotificationDetails(android: _androidAlarmDetails),
      payload: 'test',
    );
    debugPrint('[Notification] Instant test notification sent.');
  }

  /// Schedule a notification 5 seconds from now to test exact alarm delivery.
  Future<void> sendTestScheduledNotification() async {
    if (kIsWeb) return;
    if (!_initialized) await init();

    final fireAt = DateTime.now().toUtc().add(const Duration(seconds: 5));
    final tzScheduled = tz.TZDateTime.from(fireAt, tz.UTC);

    try {
      await _plugin.zonedSchedule(
        900002,
        '⏰ RemindMe Alarm Test',
        'Exact alarm is working! Tasks will alert you on time.',
        tzScheduled,
        NotificationDetails(android: _androidAlarmDetails),
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        uiLocalNotificationDateInterpretation:
            UILocalNotificationDateInterpretation.absoluteTime,
        payload: 'test_scheduled',
      );
      debugPrint('[Notification] 5-second test alarm scheduled at $tzScheduled');
    } catch (e) {
      debugPrint('[Notification] 5-second test scheduling failed: $e');
    }
  }

  Future<void> cancelNotification(String id) async {
    if (kIsWeb) {
      web_notifier.cancelWebNotification(id);
      return;
    }
    try {
      if (!_initialized) {
        await init();
      }
      await _plugin.cancel(id.hashCode & 0x7FFFFFFF);
      debugPrint('[Notification] Cancelled: ID $id');
    } catch (e) {
      debugPrint('[Notification] Cancel notification failed: $e');
    }
  }

  Future<void> cancelAll() async {
    if (kIsWeb) {
      web_notifier.cancelAllWebNotifications();
      return;
    }
    try {
      if (!_initialized) {
        await init();
      }
      await _plugin.cancelAll();
      debugPrint('[Notification] Cancelled all notifications');
    } catch (e) {
      debugPrint('[Notification] Cancel all notifications failed: $e');
    }
  }
}
