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
  final List<String> _filters = [
    'all',
    'created',
    'completed',
    'deleted',
    'edited',
    'snoozed',
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
    final logs = _filteredLogs(state.auditLogs);

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
                  backgroundColor: colors.surfaceContainerHighest.withValues(alpha: 0.1),
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
                      child: Icon(Icons.analytics_rounded, size: 20, color: colors.primary),
                    ),
                    const SizedBox(width: 12),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          state.auditPeriod == 'month' ? 'MONTHLY PERFORMANCE' : 'WEEKLY PERFORMANCE',
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
                      icon: Icons.task_alt_rounded,
                      value: '${state.analytics?.completedThisWeek ?? 0}',
                      label: 'Done',
                      color: Colors.white,
                    ),
                    _AuditStat(
                      icon: Icons.add_circle_outline_rounded,
                      value: '${state.analytics?.createdThisWeek ?? 0}',
                      label: 'Added',
                      color: Colors.white.withValues(alpha: 0.9),
                    ),
                    _AuditStat(
                      icon: Icons.snooze_rounded,
                      value: '${state.analytics?.snoozedThisWeek ?? 0}',
                      label: 'Snoozed',
                      color: Colors.white.withValues(alpha: 0.8),
                    ),
                    _AuditStat(
                      icon: Icons.error_outline_rounded,
                      value: '${state.analytics?.audit['missed_tasks'] ?? 0}',
                      label: 'Missed',
                      color: Colors.white.withValues(alpha: 0.7),
                    ),
                    _AuditStat(
                      icon: Icons.notifications_active_rounded,
                      value: '${state.analytics?.audit['notifications_sent'] ?? 0}',
                      label: 'Notifs',
                      color: Colors.white.withValues(alpha: 0.6),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // ── Filters Section ────────────────────────────────────────
          SliverToBoxAdapter(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 16),
              child: Row(
                children: _filters.map((f) {
                  final isSelected = _filter == f;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: FilterChip(
                      label: Text(f.replaceAll('_', ' ').toUpperCase()),
                      selected: isSelected,
                      onSelected: (val) => setState(() => _filter = f),
                      labelStyle: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: isSelected ? Colors.white : colors.onSurfaceVariant,
                      ),
                      backgroundColor: colors.surfaceContainerHighest.withValues(alpha: 0.5),
                      selectedColor: colors.primary,
                      showCheckmark: false,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      side: BorderSide.none,
                    ),
                  );
                }).toList(),
              ),
            ),
          ),

          // ── Logs List ───────────────────────────────────────────────
          if (logs.isEmpty)
            SliverFillRemaining(
              hasScrollBody: false,
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(32),
                      decoration: BoxDecoration(
                        color: colors.primary.withValues(alpha: 0.05),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(Icons.auto_graph_rounded, size: 80, color: colors.primary.withValues(alpha: 0.2)),
                    ),
                    const SizedBox(height: 32),
                    Text(
                      'No Activity Records',
                      style: GoogleFonts.outfit(
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                        color: colors.onSurface,
                        letterSpacing: -0.5,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 48),
                      child: Text(
                        'Your digital footprint is currently clear. Complete tasks or interact with the AI to see your productivity audit trail.',
                        textAlign: TextAlign.center,
                        style: GoogleFonts.outfit(
                          fontSize: 14,
                          color: colors.onSurfaceVariant.withValues(alpha: 0.6),
                          height: 1.5,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) => _AuditLogTile(log: logs[index], filter: _filter),
                  childCount: logs.length,
                ),
              ),
            ),
          
          const SliverPadding(padding: EdgeInsets.only(bottom: 32)),
        ],
      ),
    );
  }

  List<AuditLog> _filteredLogs(List<AuditLog> logs) {
    if (_filter == 'all') return logs;
    
    return logs.where((log) {
      final event = log.event.toLowerCase();
      switch (_filter) {
        case 'created': return event == 'task_created' || event == 'created';
        case 'completed': return event == 'task_completed' || event == 'completed';
        case 'deleted': return event == 'task_deleted' || event == 'deleted';
        case 'edited': return event == 'task_edited' || event == 'edited';
        case 'snoozed': return event == 'task_snoozed' || event == 'snoozed';
        default: return event == _filter;
      }
    }).toList();
  }
}

class _AuditStat extends StatelessWidget {
  const _AuditStat({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String value;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 65,
      child: Column(
        children: [
          Icon(icon, size: 20, color: color),
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
              fontSize: 11,
              color: color.withValues(alpha: 0.7),
            ),
          ),
        ],
      ),
    );
  }
}

class _AuditLogTile extends StatelessWidget {
  const _AuditLogTile({required this.log, required this.filter});

  final AuditLog log;
  final String filter;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final time = DateFormat('MMM d, h:mm a').format(log.timestamp);

    IconData icon;
    Color iconColor;
    final event = log.event.startsWith('task_') ? log.event.substring(5) : log.event;
    switch (event) {
      case 'created':
        icon = Icons.add_circle_rounded;
        iconColor = Colors.green;
        break;
      case 'completed':
        icon = Icons.check_circle_rounded;
        iconColor = Colors.green;
        break;
      case 'deleted':
        icon = Icons.delete_rounded;
        iconColor = Colors.red;
        break;
      case 'edited':
        icon = Icons.edit_rounded;
        iconColor = Colors.blue;
        break;
      case 'notified':
      case 'notification_scheduled':
        icon = Icons.notifications_active_rounded;
        iconColor = Colors.purple;
        break;
      case 'missed':
        icon = Icons.warning_amber_rounded;
        iconColor = Colors.red;
        break;
      case 'snoozed':
        icon = Icons.snooze_rounded;
        iconColor = Colors.amber;
        break;
      case 'dismissed':
        icon = Icons.cancel_rounded;
        iconColor = Colors.grey;
        break;
      default:
        icon = Icons.info_rounded;
        iconColor = colors.onSurfaceVariant;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Card(
        elevation: 0,
        color: colors.surfaceContainerLowest.withValues(alpha: 0.5),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: colors.outlineVariant.withValues(alpha: 0.2)),
        ),
        child: ListTile(
          visualDensity: VisualDensity.compact,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 0),
          leading: Icon(icon, size: 18, color: iconColor),
          title: Text(
            filter == 'all' ? log.eventLabel : log.taskTitle,
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
          ),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                time,
                style: TextStyle(fontSize: 11, color: colors.onSurfaceVariant.withValues(alpha: 0.7)),
              ),
              if (log.notificationScheduledAt != null || log.notificationSentAt != null)
                Padding(
                  padding: const EdgeInsets.only(top: 2),
                  child: Text(
                    'Scheduled: ${log.notificationScheduledAt ?? "N/A"} • Sent: ${log.notificationSentAt ?? "N/A"}',
                    style: TextStyle(fontSize: 10, color: colors.primary.withValues(alpha: 0.6)),
                  ),
                ),
            ],
          ),
          trailing: const SizedBox.shrink(),
        ),
      ),
    ).animate().fadeIn(duration: 400.ms).slideX(begin: 0.05, end: 0);
  }
}
