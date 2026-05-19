import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../core/app_state.dart';
import '../models/analytics_summary.dart';
import '../models/task.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final analytics = state.analytics;
    final colors = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return CustomScrollView(
      slivers: [
        // ── Premium Greeting Header ──────────────────────────────
        SliverToBoxAdapter(
          child: Container(
            padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: isDark
                    ? [const Color(0xFF0F172A), const Color(0xFF1E293B)]
                    : [colors.primary, colors.primary.withValues(alpha: 0.8)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius:
                  const BorderRadius.vertical(bottom: Radius.circular(32)),
              boxShadow: [
                BoxShadow(
                  color: colors.primary.withValues(alpha: 0.2),
                  blurRadius: 20,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _greeting(),
                        style: GoogleFonts.montserrat(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: Colors.white.withValues(alpha: 0.7),
                        ),
                      ),
                      Text(
                        state.displayName ?? state.username ?? 'there',
                        style: GoogleFonts.montserrat(
                          fontSize: 28,
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                          letterSpacing: -0.5,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        DateFormat('EEEE, d MMMM y').format(DateTime.now()),
                        style: GoogleFonts.montserrat(
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                          color: Colors.white.withValues(alpha: 0.5),
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                    border:
                        Border.all(color: Colors.white.withValues(alpha: 0.2)),
                  ),
                  child: Center(
                    child: state.avatarEmoji != null &&
                            state.avatarEmoji!.isNotEmpty
                        ? (state.avatarEmoji!.contains('avatars/')
                            ? ClipRRect(
                                borderRadius: BorderRadius.circular(20),
                                child: Image.asset(
                                  state.avatarEmoji!.startsWith('assets/')
                                      ? state.avatarEmoji!
                                      : 'assets/${state.avatarEmoji!}',
                                  fit: BoxFit.cover,
                                  errorBuilder: (context, error, stackTrace) =>
                                      const Icon(Icons.person_rounded),
                                ),
                              )
                            : Text(
                                state.avatarEmoji!,
                                style: const TextStyle(fontSize: 32),
                              ))
                        : ClipRRect(
                            borderRadius: BorderRadius.circular(20),
                            child: Image.asset(
                              'assets/logo.png',
                              fit: BoxFit.contain,
                            ),
                          ),
                  ),
                ),
              ],
            ),
          )
              .animate(onPlay: (c) => c.repeat(reverse: true))
              .shimmer(duration: 3000.ms, color: Colors.white12),
        ),


        if (analytics != null)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
              child: _buildCompletionGauge(analytics, colors),
            ),
          ),

        // ── Stats Row ────────────────────────────────────────────
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
            child: _buildStatsRow(analytics, colors),
          ),
        ),

        // ── Today's Tasks ────────────────────────────────────────
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 28, 20, 0),
            child: _buildSectionHeader(
                context, "Today's Focus", 'Priority items due today'),
          ),
        ),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
            child: _buildTodayTasks(state, colors, isDark),
          ),
        ),

        // ── Weekly Chart ─────────────────────────────────────────
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 28, 20, 0),
            child: _buildSectionHeader(
                context, 'Weekly Activity', analytics?.weeklyRange ?? ''),
          ),
        ),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
            child: _buildWeeklyChart(analytics, colors),
          ),
        ),

        // ── AI Insight ───────────────────────────────────────────
        if (analytics != null && analytics.aiInsight.isNotEmpty)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 28, 20, 0),
              child: _buildAIInsightCard(analytics.aiInsight, colors),
            ),
          ),

        // ── Overview Pie ─────────────────────────────────────────
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 28, 20, 0),
            child: _buildSectionHeader(
                context, 'Task Overview', 'Completion breakdown'),
          ),
        ),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
            child: _buildOverviewPie(analytics, colors),
          ),
        ),
      ],
    );
  }

  String _greeting() {
    final h = DateTime.now().hour;
    if (h >= 5 && h < 12) return 'Good morning,';
    if (h >= 12 && h < 17) return 'Good afternoon,';
    if (h >= 17 && h < 21) return 'Good evening,';
    return 'Good night,';
  }

  Widget _buildStatsRow(AnalyticsSummary? analytics, ColorScheme colors) {
    return Row(
      children: [
        Expanded(
          child: _StatCard(
            icon: Icons.pending_actions_rounded,
            label: 'PENDING',
            value: '${analytics?.pending ?? 0}',
            color: const Color(0xFFFF7043),
            gradient: const [Color(0xFFFF7043), Color(0xFFFFB199)],
            percent: analytics != null && analytics.totalTasks > 0
                ? (analytics.pending / analytics.totalTasks * 100).toInt()
                : 0,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _StatCard(
            icon: Icons.rocket_launch_rounded,
            label: 'UPCOMING',
            value: '${analytics?.upcoming ?? 0}',
            color: const Color(0xFF42A5F5),
            gradient: const [Color(0xFF42A5F5), Color(0xFF72C2FF)],
            percent: analytics != null && analytics.totalTasks > 0
                ? (analytics.upcoming / analytics.totalTasks * 100).toInt()
                : 0,
          ),
        ),
      ],
    );
  }

  Widget _buildTodayTasks(AppState state, ColorScheme colors, bool isDark) {
    final now = DateTime.now();
    final nowStr = DateFormat('yyyy-MM-dd').format(now);
    final tomorrowStr =
        DateFormat('yyyy-MM-dd').format(now.add(const Duration(days: 1)));

    final todayTasks = state.tasks.where((t) {
      final taskDateStr = DateFormat('yyyy-MM-dd').format(t.dueAt.toLocal());
      // Be lenient: show tasks that might have shifted slightly due to UTC storage
      // If it's technically "tomorrow" but in the first 5 hours, it might be a UTC-shifted "today" task
      return (taskDateStr == nowStr ||
              (t.dueAt.toLocal().hour < 5 && taskDateStr == tomorrowStr)) &&
          !t.isCompleted;
    }).toList();

    if (todayTasks.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(28),
        decoration: BoxDecoration(
          color: isDark
              ? Colors.white.withValues(alpha: 0.04)
              : Colors.black.withValues(alpha: 0.03),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.grey.withValues(alpha: 0.12)),
        ),
        child: Column(
          children: [
            Icon(Icons.celebration_rounded,
                size: 40, color: colors.primary.withValues(alpha: 0.5)),
            const SizedBox(height: 10),
            Text(
              'All clear for today! 🎉',
              style: TextStyle(
                color: colors.onSurfaceVariant,
                fontWeight: FontWeight.w600,
                fontSize: 15,
              ),
            ),
          ],
        ),
      ).animate().fadeIn(duration: 500.ms);
    }

    return Column(
      children: todayTasks
          .take(3)
          .map((task) => _DashboardTaskCard(task: task))
          .toList(),
    );
  }

  Widget _buildCompletionGauge(AnalyticsSummary analytics, ColorScheme colors) {
    final rate = analytics.completionPercentage;
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(32),
        gradient: LinearGradient(
          colors: [
            colors.primary,
            colors.primary.withValues(alpha: 0.8),
            colors.tertiary.withValues(alpha: 0.9),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: [
          BoxShadow(
            color: colors.primary.withValues(alpha: 0.3),
            blurRadius: 30,
            offset: const Offset(0, 15),
          ),
        ],
      ),
      child: Stack(
        children: [
          Positioned(
            right: -20,
            top: -20,
            child: Icon(
              Icons.auto_awesome_rounded,
              size: 100,
              color: Colors.white.withValues(alpha: 0.1),
            ),
          ),
          Row(
            children: [
              Stack(
                alignment: Alignment.center,
                children: [
                  // 3D Inner Shadow effect
                  Container(
                    width: 90,
                    height: 90,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.2),
                          blurRadius: 10,
                        ),
                      ],
                    ),
                  ),
                  SizedBox(
                    width: 90,
                    height: 90,
                    child: CircularProgressIndicator(
                      value: rate / 100,
                      strokeWidth: 10,
                      backgroundColor: Colors.white.withValues(alpha: 0.1),
                      valueColor:
                          const AlwaysStoppedAnimation<Color>(Colors.white),
                      strokeCap: StrokeCap.round,
                    ),
                  ),
                  // Glow effect
                  Container(
                    width: 90,
                    height: 90,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.white.withValues(alpha: 0.1),
                          blurRadius: 20,
                          spreadRadius: -5,
                        ),
                      ],
                    ),
                  ),
                  Text(
                    '${rate.toStringAsFixed(0)}%',
                    style: GoogleFonts.montserrat(
                      fontWeight: FontWeight.w900,
                      fontSize: 22,
                      color: Colors.white,
                      shadows: [
                        const Shadow(
                            color: Colors.black26,
                            offset: Offset(0, 2),
                            blurRadius: 4),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 24),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Daily Progress',
                      style: GoogleFonts.montserrat(
                        fontWeight: FontWeight.w800,
                        fontSize: 20,
                        color: Colors.white,
                        letterSpacing: -0.5,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '${analytics.completed} of ${analytics.totalTasks} tasks done',
                      style: GoogleFonts.montserrat(
                        color: Colors.white.withValues(alpha: 0.8),
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 14),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        rate >= 100 ? "Goal Reached! 🚀" : "Keep going! ✨",
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    ).animate().fadeIn(duration: 600.ms).slideY(begin: 0.1, end: 0);
  }

  Widget _buildAIInsightCard(String insight, ColorScheme colors) {
    if (insight.isEmpty) return const SizedBox.shrink();

    final cards =
        insight.split('\n\n').where((s) => s.trim().isNotEmpty).toList();

    return Column(
      children: cards.map((item) {
        return Container(
          width: double.infinity,
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: colors.surface,
            borderRadius: BorderRadius.circular(24),
            boxShadow: [
              BoxShadow(
                color: colors.shadow.withValues(alpha: 0.04),
                blurRadius: 16,
                offset: const Offset(0, 8),
              ),
            ],
            border: Border.all(
              color: colors.outlineVariant.withValues(alpha: 0.5),
              width: 1,
            ),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: colors.secondaryContainer.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(Icons.tips_and_updates_rounded,
                    color: colors.secondary, size: 22),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _formatInsightText(item, colors),
                  ],
                ),
              ),
            ],
          ),
        );
      }).toList(),
    ).animate().fadeIn(duration: 600.ms).slideY(begin: 0.05, end: 0);
  }

  Widget _formatInsightText(String text, ColorScheme colors) {
    final lines = text.split('\n');
    final title = lines[0];
    final body = lines.length > 1 ? lines.sublist(1).join('\n') : '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title.replaceAll('**', ''),
          style: GoogleFonts.montserrat(
            fontWeight: FontWeight.w800,
            fontSize: 15,
            color: colors.onSurface,
            letterSpacing: -0.2,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          body.replaceAll('**', ''),
          style: TextStyle(
            fontSize: 14,
            height: 1.5,
            fontWeight: FontWeight.w500,
            color: colors.onSurfaceVariant.withValues(alpha: 0.8),
          ),
        ),
      ],
    );
  }

  Widget _buildSectionHeader(
      BuildContext context, String title, String subtitle) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: GoogleFonts.montserrat(
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
        if (subtitle.isNotEmpty) ...[
          const SizedBox(height: 2),
          Text(
            subtitle,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
        ],
      ],
    );
  }

  Widget _buildWeeklyChart(AnalyticsSummary? analytics, ColorScheme colors) {
    if (analytics == null || analytics.weeklyLabels.isEmpty) {
      return Container(
        height: 180,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          color: colors.surfaceContainerLowest,
        ),
        child: const Center(child: Text('No weekly data yet')),
      );
    }
    final maxVal =
        analytics.weeklyCounts.reduce((a, b) => a > b ? a : b).toDouble();

    return Container(
      height: 200,
      padding: const EdgeInsets.fromLTRB(8, 16, 16, 8),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        color: colors.surfaceContainerLowest,
      ),
      child: BarChart(
        BarChartData(
          alignment: BarChartAlignment.spaceAround,
          maxY: maxVal < 1 ? 5 : maxVal + 1,
          barTouchData: BarTouchData(
            touchTooltipData: BarTouchTooltipData(
              getTooltipItem: (group, groupIndex, rod, rodIndex) =>
                  BarTooltipItem(
                '${rod.toY.toInt()} tasks',
                TextStyle(
                  color: colors.onPrimary,
                  fontWeight: FontWeight.w600,
                  fontSize: 12,
                ),
              ),
            ),
          ),
          borderData: FlBorderData(show: false),
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            horizontalInterval: 1,
            getDrawingHorizontalLine: (value) => FlLine(
              color: colors.outlineVariant.withValues(alpha: 0.3),
              strokeWidth: 1,
            ),
          ),
          titlesData: FlTitlesData(
            leftTitles:
                const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles:
                const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles:
                const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (value, meta) {
                  final i = value.toInt();
                  if (i < 0 || i >= analytics.weeklyLabels.length)
                    return const SizedBox.shrink();
                  return Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      analytics.weeklyLabels[i],
                      style: TextStyle(
                          fontSize: 11, color: colors.onSurfaceVariant),
                    ),
                  );
                },
              ),
            ),
          ),
          barGroups: [
            for (var i = 0; i < analytics.weeklyCounts.length; i++)
              BarChartGroupData(
                x: i,
                barRods: [
                  BarChartRodData(
                    toY: analytics.weeklyCounts[i].toDouble(),
                    width: 18,
                    borderRadius:
                        const BorderRadius.vertical(top: Radius.circular(6)),
                    gradient: LinearGradient(
                      colors: [
                        colors.primary.withValues(alpha: 0.7),
                        colors.primary
                      ],
                      begin: Alignment.bottomCenter,
                      end: Alignment.topCenter,
                    ),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildOverviewPie(AnalyticsSummary? analytics, ColorScheme colors) {
    if (analytics == null) return const SizedBox.shrink();
    final completed = analytics.completed.toDouble();
    final pending = analytics.pending.toDouble();
    final upcoming = analytics.upcoming.toDouble();
    final total = completed + pending + upcoming;

    if (total == 0) {
      return Container(
        height: 140,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          color: colors.surfaceContainerLowest,
        ),
        child: const Center(child: Text('No tasks to display')),
      );
    }

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        color: colors.surfaceContainerLowest,
      ),
      child: Row(
        children: [
          SizedBox(
            width: 140,
            height: 140,
            child: Stack(
              alignment: Alignment.center,
              children: [
                PieChart(
                  PieChartData(
                    sections: [
                      PieChartSectionData(
                        value: completed,
                        color: const Color(0xFF10B981),
                        radius: 35,
                        showTitle: false,
                        badgeWidget: const _PieBadge(
                            icon: Icons.check_rounded,
                            color: Color(0xFF10B981)),
                        badgePositionPercentageOffset: 1.2,
                      ),
                      PieChartSectionData(
                        value: pending,
                        color: const Color(0xFFFF7043),
                        radius: 30,
                        showTitle: false,
                        badgeWidget: const _PieBadge(
                            icon: Icons.timer_outlined,
                            color: Color(0xFFFF7043)),
                        badgePositionPercentageOffset: 1.2,
                      ),
                      PieChartSectionData(
                        value: upcoming,
                        color: const Color(0xFF38BDF8),
                        radius: 25,
                        showTitle: false,
                      ),
                    ],
                    sectionsSpace: 4,
                    centerSpaceRadius: 35,
                  ),
                ),
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      '${total.toInt()}',
                      style: GoogleFonts.montserrat(
                        fontWeight: FontWeight.w900,
                        fontSize: 24,
                        color: colors.onSurface,
                      ),
                    ),
                    Text(
                      'TOTAL',
                      style: GoogleFonts.montserrat(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: colors.onSurfaceVariant.withValues(alpha: 0.5),
                        letterSpacing: 1,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                _LegendItem(
                    color: const Color(0xFF10B981),
                    label: 'Completed',
                    value: analytics.completed),
                const SizedBox(height: 10),
                _LegendItem(
                    color: const Color(0xFFFF7043),
                    label: 'Pending',
                    value: analytics.pending),
                const SizedBox(height: 10),
                _LegendItem(
                    color: const Color(0xFF38BDF8),
                    label: 'Upcoming',
                    value: analytics.upcoming),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Helper Widgets ───────────────────────────────────────────────────────

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
    required this.gradient,
    required this.percent,
  });

  final IconData icon;
  final String label;
  final String value;
  final Color color;
  final List<Color> gradient;
  final int percent;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: isDark
            ? colors.surfaceContainerHighest.withValues(alpha: 0.3)
            : Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.1),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
        border: Border.all(
          color: color.withValues(alpha: 0.1),
          width: 1,
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            right: -10,
            bottom: -10,
            child: Icon(
              icon,
              size: 40,
              color: color.withValues(alpha: 0.05),
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: gradient,
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(14),
                      boxShadow: [
                        BoxShadow(
                          color: color.withValues(alpha: 0.25),
                          blurRadius: 8,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Icon(icon, size: 18, color: Colors.white),
                  ),
                  if (percent > 0)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: color.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        '$percent%',
                        style: TextStyle(
                          color: color,
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 20),
              Text(
                value,
                style: GoogleFonts.montserrat(
                  fontWeight: FontWeight.w900,
                  fontSize: 28,
                  color: colors.onSurface,
                  letterSpacing: -1,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                label,
                style: GoogleFonts.montserrat(
                  fontSize: 10,
                  color: colors.onSurfaceVariant.withValues(alpha: 0.7),
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
        ],
      ),
    )
        .animate()
        .fadeIn(duration: 400.ms)
        .scale(curve: Curves.easeOutBack, delay: 100.ms);
  }
}

class _DashboardTaskCard extends StatelessWidget {
  const _DashboardTaskCard({required this.task});
  final TaskItem task;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final priorityColor = Color(task.priorityColorValue);
    final isOverdue = task.isOverdue == 1 && !task.isCompleted;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color:
              isOverdue ? colors.error : priorityColor.withValues(alpha: 0.5),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: (isOverdue ? colors.error : priorityColor)
                .withValues(alpha: 0.12),
            blurRadius: 20,
            spreadRadius: -2,
            offset: const Offset(0, 10),
          ),
          BoxShadow(
            color: (isOverdue ? colors.error : priorityColor)
                .withValues(alpha: 0.08),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(18),
        child: Row(
          children: [
            Container(
              width: 6,
              height: 70,
              color: isOverdue ? colors.error : priorityColor,
            ),
            const SizedBox(width: 12),
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: task.categoryColor.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(12),
              ),
              child:
                  Icon(task.categoryIcon, color: task.categoryColor, size: 22),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    task.title,
                    style: GoogleFonts.montserrat(
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                      color: isOverdue ? colors.error : colors.onSurface,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 3),
                  Row(
                    children: [
                      const SizedBox(width: 4),
                      Text(
                        '${task.dueAt.hour.toString().padLeft(2, '0')}:${task.dueAt.minute.toString().padLeft(2, '0')}',
                        style: TextStyle(
                          color: isOverdue
                              ? colors.error
                              : colors.onSurfaceVariant,
                          fontSize: 12,
                          fontWeight:
                              isOverdue ? FontWeight.w600 : FontWeight.w500,
                        ),
                      ),
                      if (isOverdue) ...[
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: colors.error.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            'OVERDUE',
                            style: TextStyle(
                              color: colors.error,
                              fontSize: 9,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  visualDensity: VisualDensity.compact,
                  icon:
                      const Icon(Icons.check_circle_outline_rounded, size: 20),
                  color: Colors.green,
                  onPressed: () => context.read<AppState>().completeTask(task),
                ),
                IconButton(
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(Icons.delete_outline_rounded, size: 20),
                  color: colors.error,
                  onPressed: () => _confirmDelete(context, task),
                ),
              ],
            ),
          ],
        ),
      ),
    ).animate().fadeIn(duration: 350.ms).slideX(begin: 0.05, end: 0);
  }

  void _confirmDelete(BuildContext context, TaskItem task) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Task'),
        content: Text('Are you sure you want to delete "${task.title}"?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              context.read<AppState>().deleteTask(task);
              Navigator.pop(ctx);
            },
            style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}

class _LegendItem extends StatelessWidget {
  const _LegendItem({
    required this.color,
    required this.label,
    required this.value,
  });

  final Color color;
  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
              color: color, borderRadius: BorderRadius.circular(3)),
        ),
        const SizedBox(width: 8),
        Expanded(child: Text(label, style: const TextStyle(fontSize: 13))),
        Text('$value',
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
      ],
    );
  }
}

class _PieBadge extends StatelessWidget {
  const _PieBadge({required this.icon, required this.color});
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.white,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.3),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Icon(icon, size: 12, color: color),
    );
  }
}
