import 'package:flutter/material.dart';

class TaskItem {
  const TaskItem({
    required this.id,
    required this.title,
    required this.dueIso,
    required this.priority,
    required this.notified,
    this.createdIso,
    this.completedIso,
    required this.category,
    required this.sound,
    required this.description,
    required this.isOverdue,
    this.status = 'open',
    this.notificationStatus = 'pending',
  });

  final String id;
  final String title;
  final String dueIso;
  final int priority;
  final int notified;
  final String? createdIso;
  final String? completedIso;
  final String category;
  final String sound;
  final String description;
  final int isOverdue;
  final String status;
  final String notificationStatus;

  bool get isCompleted => status == 'completed' || (completedIso != null && completedIso!.isNotEmpty);
  bool get isNotified => notificationStatus == 'sent' || notified == 1;
  bool get isMissed => notificationStatus == 'missed' || isOverdue == 1;

  DateTime get dueAt => DateTime.parse(dueIso).toLocal();
  DateTime? get completedAt => (completedIso != null && completedIso!.isNotEmpty) ? DateTime.parse(completedIso!).toLocal() : null;

  String get displayStatus {
    if (isCompleted) return 'Completed';
    final now = DateTime.now();
    final diff = dueAt.difference(now);
    
    if (diff.isNegative) {
      if (diff.inMinutes.abs() < 5) return 'Due Now';
      return 'Missed';
    }
    if (diff.inMinutes < 5) return 'Due Soon';
    return 'Upcoming';
  }

  String get priorityLabel {
    switch (priority) {
      case 1:
        return 'High';
      case 2:
        return 'Medium';
      default:
        return 'Low';
    }
  }

  int get priorityColorValue {
    switch (priority) {
      case 1:
        return 0xFFFF3B30; // High = Premium Vibrant Red
      case 2:
        return 0xFFFF9500; // Medium = Vibrant Orange
      default:
        return 0xFF34C759; // Low = iOS Green
    }
  }

  IconData get categoryIcon {
    switch (category.toLowerCase()) {
      case 'gym':
      case 'workout':
      case 'fitness':
      case 'training':
      case 'sport':
      case 'sports':
      case 'run':
      case 'running':
      case 'lifting':
      case 'calisthenics':
        return Icons.fitness_center_rounded;
      case 'study':
      case 'learn':
      case 'school':
      case 'homework':
      case 'assignment':
      case 'university':
      case 'research':
        return Icons.auto_stories_rounded;
      case 'work':
      case 'office':
      case 'project':
      case 'report':
      case 'career':
        return Icons.business_center_rounded;
      case 'meeting':
      case 'sync':
      case 'standup':
      case 'discussion':
      case 'catchup':
        return Icons.groups_2_rounded;
      case 'gaming':
      case 'game':
      case 'ranked':
      case 'steam':
        return Icons.sports_esports_rounded;
      case 'finance':
      case 'payment':
      case 'bank':
      case 'bill':
      case 'salary':
      case 'invoice':
      case 'rent':
      case 'money':
        return Icons.account_balance_wallet_rounded;
      case 'health':
      case 'medicine':
      case 'doctor':
      case 'clinic':
      case 'pharmacy':
      case 'pill':
      case 'dentist':
      case 'physio':
        return Icons.medication_rounded;
      case 'home':
      case 'clean':
      case 'laundry':
      case 'cook':
      case 'dishes':
      case 'repair':
      case 'fix':
        return Icons.home_repair_service_rounded;
      case 'personal':
      case 'care':
      case 'trip':
      case 'vacation':
        return Icons.person_rounded;
      case 'call':
      case 'phone':
      case 'facetime':
        return Icons.call_rounded;
      case 'family':
      case 'mom':
      case 'dad':
      case 'parents':
        return Icons.family_restroom_rounded;
      case 'social':
      case 'party':
      case 'gathering':
      case 'event':
      case 'concert':
        return Icons.celebration_rounded;
      case 'birthday':
      case 'born':
        return Icons.cake_rounded;
      default:
        return Icons.auto_awesome_rounded;
    }
  }

  Color get categoryColor {
    switch (category.toLowerCase()) {
      case 'gym': return const Color(0xFFFF5722); // Deep Orange
      case 'study': return const Color(0xFF6366F1); // Indigo
      case 'work': return const Color(0xFF0EA5E9); // Sky Blue
      case 'meeting': return const Color(0xFF8B5CF6); // Violet
      case 'gaming': return const Color(0xFFEC4899); // Pink
      case 'finance': return const Color(0xFF10B981); // Emerald
      case 'health': return const Color(0xFFF43F5E); // Rose
      case 'home': return const Color(0xFFF59E0B); // Amber
      case 'call': return const Color(0xFF06B6D4); // Cyan
      case 'family': return const Color(0xFF64748B); // Slate
      case 'social': return const Color(0xFFA855F7); // Purple
      case 'birthday': return const Color(0xFFFFCC00); // Gold
      case 'personal': return const Color(0xFF14B8A6); // Teal
      default: return const Color(0xFF94A3B8); // Slate
    }
  }

  factory TaskItem.fromJson(Map<String, dynamic> json) {
    return TaskItem(
      id: json['id']?.toString() ?? '',
      title: json['title'] as String? ?? 'Untitled',
      dueIso: json['due_iso'] as String? ?? '',
      priority: json['priority'] as int? ?? 2,
      notified: json['notified'] as int? ?? 0,
      createdIso: json['created_iso'] as String?,
      completedIso: json['completed_iso'] as String?,
      category: json['category'] as String? ?? 'General',
      sound: json['sound'] as String? ?? 'Default',
      description: json['description'] as String? ?? '',
      isOverdue: json['is_overdue'] as int? ?? 0,
      status: json['status'] as String? ?? 'open',
      notificationStatus: json['notification_status'] as String? ?? 'pending',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'due_iso': dueIso,
        'priority': priority,
        'notified': notified,
        'created_iso': createdIso,
        'completed_iso': completedIso,
        'category': category,
        'sound': sound,
        'description': description,
        'is_overdue': isOverdue,
        'status': status,
        'notification_status': notificationStatus,
      };
}

class TaskDraft {
  const TaskDraft({
    required this.title,
    required this.dueIso,
    required this.priority,
    required this.category,
    this.sound = 'Default',
    this.description = '',
  });

  final String title;
  final String dueIso;
  final int priority;
  final String category;
  final String sound;
  final String description;

  Map<String, dynamic> toJson() => {
        'title': title,
        'due_iso': dueIso,
        'priority': priority,
        'category': category,
        'sound': sound,
        'description': description,
      };
}
