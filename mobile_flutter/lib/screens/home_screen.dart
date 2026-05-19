import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import 'assistant_screen.dart';
import 'audit_screen.dart';
import 'calendar_screen.dart';
import 'dashboard_screen.dart';
import 'history_screen.dart';
import 'settings_screen.dart';
import 'tasks_screen.dart';

import '../core/notification_service.dart';
import '../core/app_state.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _index = 0;

  @override
  void initState() {
    super.initState();
    _requestNotificationPermission();
  }

  Future<void> _requestNotificationPermission() async {
    await NotificationService().requestPermissions();
  }

  final _screens = const [
    DashboardScreen(),
    TasksScreen(),
    CalendarScreen(),
    HistoryScreen(),
    AssistantScreen(),
    AuditScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    return Scaffold(
      appBar: _index == 0 ? null : AppBar(
        title: Text(
          _index == 1 ? 'Tasks' :
          _index == 2 ? 'Calendar' :
          _index == 3 ? 'History' :
          _index == 4 ? 'AI Assistant' :
          _index == 5 ? 'Audit Logs' : 'Settings',
          style: GoogleFonts.montserrat(
            fontWeight: FontWeight.w800,
            fontSize: 18,
            letterSpacing: -0.5,
          ),
        ),
        centerTitle: true,
        actions: const [],
      ),
      body: Column(
        children: [
          if (state.isOffline || state.isReconnecting)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
              color: state.isReconnecting ? const Color(0xFFFF9500) : const Color(0xFFFF3B30),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    state.isReconnecting ? Icons.sync : Icons.cloud_off_rounded,
                    color: Colors.white,
                    size: 16,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    state.isReconnecting
                        ? 'Reconnecting to cloud...'
                        : 'Operating in Offline Mode (Serving Cache)',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: Theme.of(context).brightness == Brightness.dark
                      ? [const Color(0xFF0F172A), const Color(0xFF111827)]
                      : [const Color(0xFFF1F5F9), const Color(0xFFE2E8F0)],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
              child: Stack(
                children: [
                  // ── Decorative Background Elements ────────────────────────
                  Positioned(
                    top: -100,
                    right: -50,
                    child: Container(
                      width: 300,
                      height: 300,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF00C2FF).withValues(alpha: 0.1),
                      ),
                    ),
                  ),
                  Positioned(
                    bottom: 100,
                    left: -80,
                    child: Container(
                      width: 250,
                      height: 250,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF38BDF8).withValues(alpha: 0.08),
                      ),
                    ),
                  ),
                  
                  // ── Main Content ──────────────────────────────────────────
                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 300),
                    child: _screens[_index],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: NavigationBarTheme(
        data: NavigationBarThemeData(
          height: 60, // Slimmer profile
          labelTextStyle: WidgetStateProperty.all(
            const TextStyle(fontSize: 9, fontWeight: FontWeight.w600, letterSpacing: -0.2),
          ),
          iconTheme: WidgetStateProperty.all(const IconThemeData(size: 20)),
        ),
        child: NavigationBar(
          selectedIndex: _index,
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow, // Show all since we made them small
          onDestinationSelected: (value) => setState(() => _index = value),
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.dashboard_outlined),
              selectedIcon: Icon(Icons.dashboard_rounded),
              label: 'Home', // Shorter than 'Dashboard'
            ),
            NavigationDestination(
              icon: Icon(Icons.checklist_outlined),
              selectedIcon: Icon(Icons.checklist_rounded),
              label: 'Tasks',
            ),
            NavigationDestination(
              icon: Icon(Icons.calendar_month_outlined),
              selectedIcon: Icon(Icons.calendar_month_rounded),
              label: 'Calendar',
            ),
            NavigationDestination(
              icon: Icon(Icons.history_outlined),
              selectedIcon: Icon(Icons.history_rounded),
              label: 'History',
            ),
            NavigationDestination(
              icon: Icon(Icons.auto_awesome_outlined),
              selectedIcon: Icon(Icons.auto_awesome_rounded),
              label: 'AI',
            ),
            NavigationDestination(
              icon: Icon(Icons.analytics_outlined),
              selectedIcon: Icon(Icons.analytics_rounded),
              label: 'Audit',
            ),
            NavigationDestination(
              icon: Icon(Icons.settings_outlined),
              selectedIcon: Icon(Icons.settings_rounded),
              label: 'Settings',
            ),
          ],
        ),
      ),
    );
  }
}
