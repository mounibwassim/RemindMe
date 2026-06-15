import 'dart:convert';

class AuditLog {
  const AuditLog({
    required this.id,
    this.taskId,
    required this.event,
    required this.timestamp,
    this.userUid,
    this.extra,
    this.notificationScheduledAt,
    this.notificationSentAt,
  });

  final String id;
  final String? taskId;
  final String event;
  final DateTime timestamp;
  final String? userUid;
  final String? extra;
  final DateTime? notificationScheduledAt;
  final DateTime? notificationSentAt;

  String get eventIcon {
    switch (event) {
      case 'created':
        return 'add_circle';
      case 'completed':
        return 'check_circle';
      case 'deleted':
        return 'delete';
      case 'edited':
        return 'edit';
      case 'notified':
      case 'notification_scheduled':
      case 'notification_triggered':
      case 'notification_sent':
        return 'notifications';
      case 'opened':
      case 'notification_opened':
        return 'visibility';
      case 'missed':
        return 'warning';
      case 'snoozed':
        return 'snooze';
      case 'dismissed':
        return 'cancel';
      default:
        return 'info';
    }
  }

  Map<String, dynamic>? get structuredDetails {
    if (extra == null || !extra!.trim().startsWith('{')) return null;
    try {
      return jsonDecode(extra!);
    } catch (_) {
      return null;
    }
  }

  String get userName => structuredDetails?['user_name'] ?? 'System';
  String get userEmail => structuredDetails?['user_email'] ?? '';
  String get actionType {
    if (structuredDetails != null) return structuredDetails!['action_type'] ?? event;
    return event.startsWith('task_') ? event.substring(5) : event;
  }
  String get module {
    if (structuredDetails != null) return structuredDetails!['module'] ?? 'Tasks';
    return event.contains('notification') ? 'Notifications' : 'Tasks';
  }
  String get recordId => structuredDetails?['record_id'] ?? taskId ?? 'N/A';
  String get previousValue => structuredDetails?['previous_value'] ?? '';
  String get newValue => structuredDetails?['new_value'] ?? '';
  String get status => structuredDetails?['status'] ?? 'Success';
  String get notes => structuredDetails?['notes'] ?? extra ?? '';

  String get cleanTaskName {
    if (structuredDetails != null) {
      final name = structuredDetails!['new_value'] ?? structuredDetails!['previous_value'] ?? '';
      if (name.isNotEmpty) return name;
    }
    final e = event.toLowerCase();
    if (e.contains('reset') || e.contains('clear')) {
      return 'System Tasks';
    }
    String label = extra ?? '';
    if (label.isEmpty) return 'Untitled Task';
    
    if (label.startsWith('Task: ')) {
      final parts = label.substring(6).split(' — ');
      return parts[0].trim();
    }
    if (label.startsWith('Created task: ')) {
      return label.substring(14).trim();
    }
    if (label.startsWith('Completed task: ')) {
      return label.substring(16).trim();
    }
    if (label.startsWith('Deleted task: ')) {
      return label.substring(13).trim();
    }
    if (label.startsWith("Snoozed '")) {
      final endIdx = label.indexOf("'", 9);
      if (endIdx != -1) {
        return label.substring(9, endIdx);
      }
    }
    if (label.startsWith('Snoozed task: ')) {
      return label.substring(14).trim();
    }
    if (label.contains('Snoozed')) {
      final match = RegExp(r"Snoozed\s+'([^']+)'").firstMatch(label);
      if (match != null) return match.group(1)!;
    }
    return label;
  }

  String get cleanActionName {
    final e = event.toLowerCase();
    if (e.contains('create') || e.contains('add')) {
      return 'created';
    }
    if (e.contains('complete')) {
      return 'completed';
    }
    if (e.contains('snooze')) {
      return 'snoozed';
    }
    if (e.contains('edit') || e.contains('updat') || e.contains('modif')) {
      return 'edited';
    }
    if (e.contains('delete') || e.contains('remov')) {
      return 'deleted';
    }
    if (e.contains('notif') || e.contains('sent') || e.contains('trigger')) {
      return 'notified';
    }
    if (e.contains('reset') || e.contains('clear')) {
      return 'reset';
    }
    return 'activity';
  }

  String get taskTitle {
    if (structuredDetails != null) {
      final val = newValue.isNotEmpty ? newValue : previousValue;
      return val.isNotEmpty ? val : 'System Event';
    }
    String label = extra ?? '';
    if (label.isNotEmpty) {
      // Clean up common prefixes and technical noise
      label = label.replaceAll(RegExp(r'^(Created|Completed|Deleted|Edited|Reopened|Snoozed|Task)\s*(task)?:\s*', caseSensitive: false), '');
      label = label.replaceAll(RegExp(r'\s*for\s+\d+m.*$', caseSensitive: false), ''); // Remove "for 10m"
      // Remove UUIDs and HEX IDs
      label = label.replaceAll(RegExp(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', caseSensitive: false), '');
      label = label.replaceAll(RegExp(r'ID:\s*[a-f0-9-]+', caseSensitive: false), ''); 
      label = label.replaceAll(RegExp(r'New time:.*$', caseSensitive: false), ''); 
      return label.trim().split(' (')[0].trim().replaceAll(RegExp(r'\s+'), ' ');
    }
    return 'Untitled Task';
  }

  String get eventLabel {
    final title = taskTitle;
    final action = actionType.replaceAll('task_', '').replaceAll('notification_', '').replaceAll('_', ' ').toUpperCase();
    if (title != 'Untitled Task' && title != 'System Event') {
      return '$title ($action)';
    }
    return action;
  }

  factory AuditLog.fromJson(Map<String, dynamic> json) {
    DateTime ts;
    try {
      final raw = json['timestamp_iso'] ?? json['created_at'] ?? json['timestamp'] ?? DateTime.now().toIso8601String();
      ts = DateTime.parse(raw).toLocal();
    } catch (e) {
      ts = DateTime.now();
    }

    DateTime? scheduled;
    if (json['notification_scheduled_at'] != null) {
      try { scheduled = DateTime.parse(json['notification_scheduled_at']).toLocal(); } catch (_) {}
    }

    DateTime? sent;
    if (json['notification_sent_at'] != null) {
      try { sent = DateTime.parse(json['notification_sent_at']).toLocal(); } catch (_) {}
    }

    return AuditLog(
      id: json['id']?.toString() ?? '',
      taskId: json['task_id']?.toString(),
      event: json['event'] ?? json['action'] ?? 'unknown',
      timestamp: ts,
      userUid: json['user_uid'] ?? json['user_id'],
      extra: json['extra'] ?? json['details'],
      notificationScheduledAt: scheduled,
      notificationSentAt: sent,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'task_id': taskId,
        'event': event,
        'timestamp_iso': timestamp.toIso8601String(),
        'user_uid': userUid,
        'extra': extra,
        'notification_scheduled_at': notificationScheduledAt?.toIso8601String(),
        'notification_sent_at': notificationSentAt?.toIso8601String(),
      };
}
