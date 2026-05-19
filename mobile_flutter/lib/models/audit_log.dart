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

  String get eventLabel {
    String label = taskTitle;
    final e = event.startsWith('task_') ? event.substring(5) : event;
    
    String action = '';
    switch (e) {
      case 'created': action = 'Created'; break;
      case 'completed': action = 'Completed'; break;
      case 'deleted': action = 'Deleted'; break;
      case 'edited': action = 'Edited'; break;
      case 'snoozed': action = 'Snoozed'; break;
      case 'reopened': action = 'Reopened'; break;
      case 'notified':
      case 'notification_triggered':
      case 'notification_sent':
        action = 'Notified'; break;
      case 'notification_scheduled': action = 'Scheduled'; break;
      default: action = e.replaceAll('_', ' ').toUpperCase();
    }

    if (label != 'Untitled Task') {
      return '$label ($action)';
    }
    return action;
  }

  // Helper for specific columns where they just want the title
  String get taskTitle {
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
