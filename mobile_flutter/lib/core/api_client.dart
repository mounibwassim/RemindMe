import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../models/analytics_summary.dart';
import '../models/assistant_reply.dart';
import '../models/audit_log.dart';
import '../models/task.dart';

class ApiClient {
  ApiClient({required this.baseUrl, this.sessionId}) {
    _shared = this;
  }

  String baseUrl;
  String? sessionId;

  static ApiClient? _shared;
  static ApiClient get shared {
    if (_shared != null) return _shared!;
    
    // Auto-detect environment base URL
    const explicitUrl = String.fromEnvironment('API_URL');
    String detectedUrl = 'https://remindme-backend-k9mb.onrender.com';
    if (explicitUrl.isNotEmpty) {
      detectedUrl = explicitUrl;
    } else if (kReleaseMode) {
      detectedUrl = 'https://remindme-backend-k9mb.onrender.com';
    } else if (kIsWeb) {
      detectedUrl = 'http://localhost:8000';
    } else {
      detectedUrl = 'http://10.0.2.2:8000'; // Sensible debug emulator default
    }

    _shared = ApiClient(baseUrl: detectedUrl);
    return _shared!;
  }

  void setSession(String? id) {
    sessionId = id;
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (sessionId != null) 'X-Session-Id': sessionId!,
      };

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  // ── Network Resilience Wrappers ──────────────────────────────────────────

  Future<http.Response> _get(String path) =>
      _safeCall(() => http.get(_uri(path), headers: _headers));

  Future<http.Response> _post(String path, {Object? body}) =>
      _safeCall(() => http.post(_uri(path), headers: _headers, body: body));

  Future<http.Response> _put(String path, {Object? body}) =>
      _safeCall(() => http.put(_uri(path), headers: _headers, body: body));

  Future<http.Response> _delete(String path) =>
      _safeCall(() => http.delete(_uri(path), headers: _headers));

  Future<http.Response> _patch(String path, {Object? body}) =>
      _safeCall(() => http.patch(_uri(path), headers: _headers, body: body));

  Future<http.Response> _safeCall(Future<http.Response> Function() call) async {
    int retries = 3;
    Duration delay = const Duration(milliseconds: 500);
    dynamic lastError;

    for (int i = 0; i < retries; i++) {
      try {
        debugPrint('ApiClient: Attempting network request (Try ${i + 1}/$retries) at $baseUrl...');
        final response = await call().timeout(const Duration(seconds: 15));
        return response;
      } catch (e) {
        lastError = e;
        debugPrint('ApiClient Connection Error (Attempt ${i + 1}/$retries): $lastError');
        if (i < retries - 1) {
          await Future.delayed(delay);
          delay *= 2; // Exponential backoff
        }
      }
    }

    throw ApiException('Network unavailable. Operating in offline mode. Details: $lastError');
  }

  // ── Authentication ────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await _post(
      '/api/v1/auth/firebase/signin',
      body: jsonEncode({
        'username': email,
        'password': password,
      }),
    );
    return _decode(response) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> devLogin(
      String username, String email, String secret) async {
    final response = await _post(
      '/api/v1/auth/dev-login',
      body: jsonEncode({
        'username': username,
        'email': email,
        'secret': secret,
      }),
    );
    return _decode(response) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> register(
      String email, String password, String name) async {
    final response = await _post(
      '/api/v1/auth/firebase/signup',
      body: jsonEncode({
        'display_name': name,
        'email': email,
        'password': password,
      }),
    );
    return _decode(response) as Map<String, dynamic>;
  }

  Future<String> forgotPassword(String username) async {
    final response = await _post(
      '/api/v1/auth/firebase/forgot-password',
      body: jsonEncode({'username': username}),
    );
    final data = _decode(response);
    return data['message'] ?? 'Check your inbox for instructions.';
  }

  Future<void> confirmPasswordReset(String code, String password,
      {String? email}) async {
    final response = await _post(
      '/api/v1/auth/firebase/confirm-password-reset',
      body: jsonEncode({
        'reset_code': code,
        'new_password': password,
        'email': email,
      }),
    );
    _decode(response);
  }

  Future<void> changePassword(
      String currentPassword, String newPassword) async {
    final response = await _post(
      '/api/v1/auth/firebase/change-password',
      body: jsonEncode({
        'current_password': currentPassword,
        'new_password': newPassword,
      }),
    );
    _decode(response);
  }

  Future<void> updateAvatar(String emoji) async {
    final response = await _patch(
      '/api/v1/auth/avatar',
      body: jsonEncode({'avatar_emoji': emoji}),
    );
    _decode(response);
  }

  // ── Tasks ─────────────────────────────────────────────────────────────────

  Future<List<TaskItem>> getTasks() async {
    final response = await _get('/api/v1/tasks');
    final data = _decode(response) as List<dynamic>;
    return data.map((item) => TaskItem.fromJson(item)).toList();
  }

  Future<TaskItem> createTask(TaskDraft draft) async {
    final response = await _post(
      '/api/v1/tasks',
      body: jsonEncode(draft.toJson()),
    );
    return TaskItem.fromJson(_decode(response));
  }

  Future<TaskItem> updateTask(String id, TaskDraft draft) async {
    final response = await _put(
      '/api/v1/tasks/$id',
      body: jsonEncode(draft.toJson()),
    );
    return TaskItem.fromJson(_decode(response));
  }

  Future<void> completeTask(String id) async {
    final response = await _post('/api/v1/tasks/$id/complete');
    _decode(response);
  }

  Future<void> reopenTask(String id) async {
    final response = await _post('/api/v1/tasks/$id/reopen');
    _decode(response);
  }

  Future<void> snoozeTask(String id, int minutes) async {
    final response = await _post(
      '/api/v1/tasks/$id/snooze',
      body: jsonEncode({'minutes': minutes}),
    );
    _decode(response);
  }

  Future<void> deleteTask(String id) async {
    final response = await _delete('/api/v1/tasks/$id');
    _decode(response);
  }

  Future<void> clearAllTasks() async {
    final response = await _delete('/api/v1/tasks/all');
    _decode(response);
  }

  // ── Assistant ─────────────────────────────────────────────────────────────

  Future<AssistantReply> sendAssistantMessage(String message) async {
    final response = await _post(
      '/api/v1/assistant/message',
      body: jsonEncode({
        'message': message,
        'client_time': DateTime.now().toIso8601String(),
      }),
    );
    return AssistantReply.fromJson(_decode(response));
  }

  Future<void> resetAssistantState() async {
    final response = await _post('/api/v1/assistant/reset');
    _decode(response);
  }

  // ── Analytics ─────────────────────────────────────────────────────────────

  Future<AnalyticsSummary> getAnalyticsSummary() async {
    final response = await _get('/api/v1/analytics/summary');
    return AnalyticsSummary.fromJson(_decode(response));
  }

  Future<List<AuditLog>> getAuditLogs({int limit = 50}) async {
    final response = await _get('/api/v1/analytics/audit?limit=$limit');
    final data = _decode(response) as List<dynamic>;
    return data.map((item) => AuditLog.fromJson(item)).toList();
  }

  Future<void> resetAnalytics() async {
    final response = await _post('/api/v1/analytics/reset');
    _decode(response);
  }

  Future<void> deleteAuditLog(String id) async {
    final response = await _delete('/api/v1/analytics/audit/$id');
    _decode(response);
  }

  Future<void> clearAuditLogs() async {
    final response = await _delete('/api/v1/analytics/audit');
    _decode(response);
  }

  Future<void> logError(String message, {String level = 'ERROR'}) async {
    try {
      await http.post(
        _uri('/api/v1/system/log'),
        headers: _headers,
        body: jsonEncode({'message': message, 'level': level}),
      ).timeout(const Duration(seconds: 3));
    } catch (_) {}
  }

  Future<String> getLogs() async {
    final response = await _get('/api/v1/system/logs');
    final data = _decode(response);
    return data['logs'] as String;
  }

  Future<void> logNotificationEvent(String taskId, String event,
      {String extra = ''}) async {
    final response = await _post(
      '/api/v1/tasks/$taskId/notification-event',
      body: jsonEncode({
        'event': event,
        'extra': extra,
      }),
    );
    _decode(response);
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  dynamic _decode(http.Response response) {
    final body = response.body.isEmpty ? null : jsonDecode(response.body);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = body is Map<String, dynamic> ? body['detail'] : null;
      throw ApiException(detail?.toString() ?? 'Request failed');
    }
    return body;
  }
}

class ApiException implements Exception {
  ApiException(this.message);
  final String message;
  @override
  String toString() => message;
}
