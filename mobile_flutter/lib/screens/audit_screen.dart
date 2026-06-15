import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../core/app_state.dart';
import '../models/audit_log.dart';

class AuditScreen extends StatefulWidget {
  const AuditScreen({super.key});

  @override
  State<AuditScreen> createState() => _AuditScreenState();
}

class _AuditScreenState extends State<AuditScreen> {
  String _filter = 'all';

  // Filter tabs matching the reference image
  final List<_FilterTab> _filterTabs = const [
    _FilterTab(key: 'all', label: 'ALL'),
    _FilterTab(key: 'created', label: 'CREATED'),
    _FilterTab(key: 'completed', label: 'COMPLETED'),
    _FilterTab(key: 'deleted', label: 'DELETED'),
    _FilterTab(key: 'edited', label: 'EDITED'),
    _FilterTab(key: 'snoozed', label: 'SNOOZED'),
    _FilterTab(key: 'notified', label: 'NOTIFIED'),
  ];

  String _getPeriodRange(String period) {
    final now = DateTime.now();
    if (period == 'month') {
      final firstDay = DateTime(now.year, now.month, 1);
      final lastDay = DateTime(now.year, now.month + 1, 0);
      final format = DateFormat('MMM d');
      final yearFormat = DateFormat('y');
      return '${format.format(firstDay)} - ${format.format(lastDay)}, ${yearFormat.format(lastDay)}';
    } else {
      final monday = now.subtract(Duration(days: now.weekday - 1));
      final sunday = monday.add(const Duration(days: 6));
      final format = DateFormat('MMM d');
      final yearFormat = DateFormat('y');
      return '${format.format(monday)} - ${format.format(sunday)}, ${yearFormat.format(sunday)}';
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final colors = Theme.of(context).colorScheme;
    final logs = _filteredLogs(state.auditLogs, state.auditPeriod);

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: CustomScrollView(
        slivers: [
          // ── Period Selector Segmented Button ──────────────────────
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
              child: SegmentedButton<String>(
                style: SegmentedButton.styleFrom(
                  backgroundColor:
                      colors.surfaceContainerHighest.withValues(alpha: 0.1),
                  selectedBackgroundColor: colors.primary,
                  selectedForegroundColor: colors.onPrimary,
                  textStyle: GoogleFonts.montserrat(
                    fontWeight: FontWeight.w700,
                    fontSize: 12,
                  ),
                ),
                segments: const [
                  ButtonSegment<String>(
                    value: 'week',
                    label: Text('Current Week'),
                    icon: Icon(Icons.view_week_rounded, size: 18),
                  ),
                  ButtonSegment<String>(
                    value: 'month',
                    label: Text('Current Month'),
                    icon: Icon(Icons.calendar_month_rounded, size: 18),
                  ),
                ],
                selected: {state.auditPeriod},
                onSelectionChanged: (newSelection) {
                  state.setAuditPeriod(newSelection.first);
                },
              ),
            ),
          ),

          // ── Weekly/Monthly Performance Header ────────────────────────
          if (state.analytics != null)
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(24, 20, 24, 12),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: colors.primary.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(Icons.analytics_rounded,
                          size: 20, color: colors.primary),
                    ),
                    const SizedBox(width: 12),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          state.auditPeriod == 'month'
                              ? 'MONTHLY PERFORMANCE'
                              : 'WEEKLY PERFORMANCE',
                          style: GoogleFonts.montserrat(
                            fontWeight: FontWeight.w900,
                            fontSize: 14,
                            letterSpacing: 1.5,
                            color: colors.onSurface,
                          ),
                        ),
                        Text(
                          _getPeriodRange(state.auditPeriod),
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: colors.primary,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
              child: Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(32),
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      colors.primary,
                      colors.primary.withValues(alpha: 0.8),
                      const Color(0xFF0EA5E9),
                    ],
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: colors.primary.withValues(alpha: 0.3),
                      blurRadius: 30,
                      offset: const Offset(0, 15),
                    ),
                  ],
                ),
                child: Wrap(
                  alignment: WrapAlignment.spaceAround,
                  runSpacing: 16,
                  children: [
                    _AuditStat(
                      icon: Icons.history_rounded,
                      value: '${state.analytics?.audit['total_actions'] ?? 0}',
                      label: 'All',
                      color: Colors.white,
                      onTap: () => setState(() => _filter = 'all'),
                    ),
                    _AuditStat(
                      icon: Icons.add_circle_outline_rounded,
                      value: '${state.analytics?.createdThisWeek ?? 0}',
                      label: 'Added',
                      color: Colors.white.withValues(alpha: 0.9),
                      onTap: () => setState(() => _filter = 'created'),
                    ),
                    _AuditStat(
                      icon: Icons.task_alt_rounded,
                      value: '${state.analytics?.completedThisWeek ?? 0}',
                      label: 'Completed',
                      color: Colors.white.withValues(alpha: 0.8),
                      onTap: () => setState(() => _filter = 'completed'),
                    ),
                    _AuditStat(
                      icon: Icons.snooze_rounded,
                      value: '${state.analytics?.snoozedThisWeek ?? 0}',
                      label: 'Snoozed',
                      color: Colors.white.withValues(alpha: 0.7),
                      onTap: () => setState(() => _filter = 'snoozed'),
                    ),
                    _AuditStat(
                      icon: Icons.restart_alt_rounded,
                      value: '${state.analytics?.audit['reset_events'] ?? 0}',
                      label: 'Reset',
                      color: Colors.white.withValues(alpha: 0.6),
                      onTap: () => setState(() => _filter = 'all'),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // ── Filter Tabs (ALL / CREATED / COMPLETED / DELETED / EDITED / SNOOZED) ──
          SliverToBoxAdapter(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
              child: Row(
                children: _filterTabs.map((tab) {
                  final isSelected = _filter == tab.key;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: GestureDetector(
                      onTap: () => setState(() => _filter = tab.key),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 16, vertical: 8),
                        decoration: BoxDecoration(
                          color: isSelected
                              ? colors.primary
                              : colors.surfaceContainerHighest
                                  .withValues(alpha: 0.4),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          tab.label,
                          style: GoogleFonts.montserrat(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: isSelected
                                ? Colors.white
                                : colors.onSurfaceVariant,
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),

          // ── Logs count label ────────────────────────────────────────
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 12),
              child: Text(
                '${logs.length} ${logs.length == 1 ? 'entry' : 'entries'}',
                style: GoogleFonts.outfit(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: colors.onSurfaceVariant,
                ),
              ),
            ),
          ),

          // ── Logs List ───────────────────────────────────────────────
          logs.isEmpty
              ? SliverFillRemaining(
                  hasScrollBody: false,
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.history_rounded,
                            size: 48,
                            color: colors.onSurfaceVariant.withValues(alpha: 0.3)),
                        const SizedBox(height: 12),
                        Text(
                          'No logs found',
                          style: GoogleFonts.outfit(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: colors.onSurfaceVariant
                                .withValues(alpha: 0.5),
                          ),
                        ),
                      ],
                    ),
                  ),
                )
              : SliverPadding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  sliver: SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) => _AuditLogTile(
                        log: logs[index],
                        index: index,
                      ),
                      childCount: logs.length,
                    ),
                  ),
                ),

          const SliverPadding(padding: EdgeInsets.only(bottom: 32)),
        ],
      ),
    );
  }

  bool _isLogInPeriod(AuditLog log, String period) {
    final now = DateTime.now();
    final logDate = log.timestamp.toLocal();
    if (period == 'month') {
      final start = DateTime(now.year, now.month, 1);
      final end = DateTime(now.year, now.month + 1, 1)
          .subtract(const Duration(microseconds: 1));
      return logDate.isAfter(start.subtract(const Duration(microseconds: 1))) &&
          logDate.isBefore(end);
    } else {
      final monday = now.subtract(Duration(days: now.weekday - 1));
      final start = DateTime(monday.year, monday.month, monday.day);
      final end = start
          .add(const Duration(days: 7))
          .subtract(const Duration(microseconds: 1));
      return logDate.isAfter(start.subtract(const Duration(microseconds: 1))) &&
          logDate.isBefore(end);
    }
  }

  List<AuditLog> _filteredLogs(List<AuditLog> logs, String period) {
    final periodLogs =
        logs.where((log) => _isLogInPeriod(log, period)).toList();

    if (_filter == 'all') return periodLogs;

    return periodLogs.where((log) {
      final action = log.cleanActionName.toLowerCase();
      return action == _filter;
    }).toList();
  }
}

class _FilterTab {
  const _FilterTab({required this.key, required this.label});
  final String key;
  final String label;
}

class _AuditStat extends StatelessWidget {
  const _AuditStat({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String value;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        width: 72,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 22, color: color),
            const SizedBox(height: 4),
            Text(
              value,
              style: GoogleFonts.montserrat(
                fontWeight: FontWeight.w800,
                fontSize: 18,
                color: color,
              ),
            ),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w700,
                color: color.withValues(alpha: 0.8),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AuditLogTile extends StatelessWidget {
  const _AuditLogTile({required this.log, required this.index});

  final AuditLog log;
  final int index;

  IconData _getIcon() {
    final action = log.cleanActionName.toLowerCase();
    switch (action) {
      case 'created':
        return Icons.add_circle_rounded;
      case 'completed':
        return Icons.check_circle_rounded;
      case 'snoozed':
        return Icons.snooze_rounded;
      case 'notified':
        return Icons.info_rounded;
      case 'deleted':
        return Icons.delete_rounded;
      case 'edited':
        return Icons.edit_rounded;
      case 'reset':
        return Icons.restart_alt_rounded;
      default:
        return Icons.info_rounded;
    }
  }

  Color _getColor() {
    final action = log.cleanActionName.toLowerCase();
    switch (action) {
      case 'created':
        return const Color(0xFF22C55E); // green
      case 'completed':
        return const Color(0xFF22C55E); // green (checkmark)
      case 'snoozed':
        return const Color(0xFFF59E0B); // amber
      case 'notified':
        return const Color(0xFF6B7280); // dark grey (info)
      case 'deleted':
        return const Color(0xFFEF4444); // red
      case 'edited':
        return const Color(0xFF3B82F6); // blue
      case 'reset':
        return const Color(0xFFF97316); // orange
      default:
        return const Color(0xFF9CA3AF); // grey
    }
  }

  /// Returns the action label exactly like in the reference image:
  /// "Study (Created)", "Work (Deleted)", "Sport (Completed)", etc.
  String _buildDisplayLabel() {
    final taskName = log.taskTitle;
    final action = _capitalizedAction();

    if (taskName.isNotEmpty &&
        taskName != 'Untitled Task' &&
        taskName != 'System Event') {
      return '$taskName ($action)';
    }
    return action;
  }

  String _capitalizedAction() {
    final action = log.cleanActionName;
    if (action.isEmpty) return 'Activity';
    return action[0].toUpperCase() + action.substring(1).toLowerCase();
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final timeStr = DateFormat('MMM d, h:mm a').format(log.timestamp.toLocal());
    final iconColor = _getColor();

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Card(
        elevation: 0,
        color: colors.surfaceContainerLowest.withValues(alpha: 0.5),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: BorderSide(
              color: colors.outlineVariant.withValues(alpha: 0.2)),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Circular icon container
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: iconColor.withValues(alpha: 0.12),
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: Icon(_getIcon(), size: 22, color: iconColor),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _buildDisplayLabel(),
                      style: GoogleFonts.outfit(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        color: colors.onSurface,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      timeStr,
                      style: GoogleFonts.outfit(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: colors.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      )
          .animate(delay: Duration(milliseconds: index * 40))
          .fadeIn(duration: 300.ms)
          .slideX(begin: 0.04, end: 0),
    );
  }
}
