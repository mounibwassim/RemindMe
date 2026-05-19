class AnalyticsSummary {
  const AnalyticsSummary({
    required this.totalTasks,
    required this.completed,
    required this.pending,
    required this.upcoming,
    required this.weeklyLabels,
    required this.weeklyCounts,
    required this.weeklyRange,
    required this.audit,
    this.completionRate = 0.0,
    this.aiInsight = '',
    this.completedThisWeek = 0,
    this.snoozedThisWeek = 0,
    this.createdThisWeek = 0,
  });

  final int totalTasks;
  final int completed;
  final int pending;
  final int upcoming;
  final List<String> weeklyLabels;
  final List<int> weeklyCounts;
  final String weeklyRange;
  final Map<String, dynamic> audit;
  final double completionRate;
  final String aiInsight;
  final int completedThisWeek;
  final int snoozedThisWeek;
  final int createdThisWeek;

  double get completionPercentage =>
      totalTasks > 0 ? (completed / totalTasks) * 100 : 0.0;

  double get pendingPercentage =>
      totalTasks > 0 ? (pending / totalTasks) * 100 : 0.0;

  double get upcomingPercentage =>
      totalTasks > 0 ? (upcoming / totalTasks) * 100 : 0.0;

  AnalyticsSummary copyWith({
    int? totalTasks,
    int? completed,
    int? pending,
    int? upcoming,
    List<String>? weeklyLabels,
    List<int>? weeklyCounts,
    String? weeklyRange,
    Map<String, dynamic>? audit,
    double? completionRate,
    String? aiInsight,
    int? completedThisWeek,
    int? snoozedThisWeek,
    int? createdThisWeek,
  }) {
    return AnalyticsSummary(
      totalTasks: totalTasks ?? this.totalTasks,
      completed: completed ?? this.completed,
      pending: pending ?? this.pending,
      upcoming: upcoming ?? this.upcoming,
      weeklyLabels: weeklyLabels ?? this.weeklyLabels,
      weeklyCounts: weeklyCounts ?? this.weeklyCounts,
      weeklyRange: weeklyRange ?? this.weeklyRange,
      audit: audit ?? this.audit,
      completionRate: completionRate ?? this.completionRate,
      aiInsight: aiInsight ?? this.aiInsight,
      completedThisWeek: completedThisWeek ?? this.completedThisWeek,
      snoozedThisWeek: snoozedThisWeek ?? this.snoozedThisWeek,
      createdThisWeek: createdThisWeek ?? this.createdThisWeek,
    );
  }

  factory AnalyticsSummary.fromJson(Map<String, dynamic> json) {
    return AnalyticsSummary(
      totalTasks: json['total_tasks'] as int? ?? 0,
      completed: json['completed'] as int? ?? 0,
      pending: json['pending'] as int? ?? 0,
      upcoming: json['upcoming'] as int? ?? 0,
      weeklyLabels: List<String>.from(json['weekly_labels'] as List? ?? []),
      weeklyCounts: List<int>.from(json['weekly_counts'] as List? ?? []),
      weeklyRange: json['weekly_range'] as String? ?? '',
      audit: Map<String, dynamic>.from(json['audit'] as Map? ?? {}),
      completionRate: (json['completion_rate'] as num?)?.toDouble() ?? 0.0,
      aiInsight: json['ai_insight'] as String? ?? '',
      completedThisWeek: json['completed_this_week'] as int? ?? 0,
      snoozedThisWeek: json['snoozed_this_week'] as int? ?? 0,
      createdThisWeek: json['created_this_week'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
        'total_tasks': totalTasks,
        'completed': completed,
        'pending': pending,
        'upcoming': upcoming,
        'weekly_labels': weeklyLabels,
        'weekly_counts': weeklyCounts,
        'weekly_range': weeklyRange,
        'audit': audit,
        'completion_rate': completionRate,
        'ai_insight': aiInsight,
        'completed_this_week': completedThisWeek,
        'snoozed_this_week': snoozedThisWeek,
        'created_this_week': createdThisWeek,
      };
}
