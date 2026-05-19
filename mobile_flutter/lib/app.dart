import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import 'core/app_state.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/warmup_screen.dart';

class RemindMeApp extends StatelessWidget {
  const RemindMeApp({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    
    Widget homeScreen;
    if (state.isWarmingUp) {
      homeScreen = const WarmupScreen();
    } else {
      homeScreen = state.isSignedIn ? const HomeScreen() : const LoginScreen();
    }

    return MaterialApp(
      title: 'RemindMe',
      debugShowCheckedModeBanner: false,
      themeMode: state.themeMode,
      theme: _buildLightTheme(),
      darkTheme: _buildDarkTheme(),
      home: homeScreen,
    );
  }

  ThemeData _buildLightTheme() {
    const seed = Color(0xFF6366F1);
    final colorScheme = ColorScheme.fromSeed(
      seedColor: seed,
      brightness: Brightness.light,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: const Color(0xFFF1F5F9), // Cleaner light gray
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.transparent,
        foregroundColor: colorScheme.onSurface,
        titleTextStyle: GoogleFonts.montserrat(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: colorScheme.onSurface,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: BorderSide(color: colorScheme.outlineVariant.withValues(alpha: 0.2)),
        ),
        clipBehavior: Clip.antiAlias,
      ),
      navigationBarTheme: NavigationBarThemeData(
        elevation: 0,
        backgroundColor: Colors.white,
        indicatorColor: seed.withValues(alpha: 0.1),
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return GoogleFonts.montserrat(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: seed,
            );
          }
          return GoogleFonts.montserrat(
            fontSize: 10,
            fontWeight: FontWeight.w500,
            color: Colors.black45,
          );
        }),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        labelStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 14),
        floatingLabelStyle: const TextStyle(
          color: seed,
          fontSize: 12,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(
              color: colorScheme.outlineVariant.withValues(alpha: 0.5)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(
              color: colorScheme.outlineVariant.withValues(alpha: 0.5)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: seed, width: 2),
        ),
        errorStyle: const TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold),
        contentPadding: const EdgeInsets.fromLTRB(20, 24, 20, 16),
        alignLabelWithHint: true,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(double.infinity, 56),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          backgroundColor: seed,
          foregroundColor: Colors.white,
          textStyle: GoogleFonts.montserrat(
            fontSize: 16,
            fontWeight: FontWeight.w700,
          ),
          elevation: 4,
          shadowColor: seed.withValues(alpha: 0.4),
        ),
      ),
    );
  }

  ThemeData _buildDarkTheme() {
    const seed = Color(0xFF00C2FF); // Premium Sky Blue
    final colorScheme = ColorScheme.fromSeed(
      seedColor: seed,
      brightness: Brightness.dark,
      primary: const Color(0xFF00C2FF),
      secondary: const Color(0xFF38BDF8),
      tertiary: const Color(0xFF0EA5E9),
      surface: const Color(0xFF0F172A),
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: const Color(0xFF0F172A),
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.transparent,
        foregroundColor: Colors.white,
        titleTextStyle: GoogleFonts.montserrat(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: Colors.white,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: const Color(0xFF1E293B).withValues(alpha: 0.6),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: BorderSide(color: Colors.white.withValues(alpha: 0.08)),
        ),
        clipBehavior: Clip.antiAlias,
        shadowColor: Colors.black.withValues(alpha: 0.4),
      ),
      navigationBarTheme: NavigationBarThemeData(
        elevation: 0,
        backgroundColor: const Color(0xFF0F172A),
        indicatorColor: const Color(0xFF00C2FF).withValues(alpha: 0.15),
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return GoogleFonts.montserrat(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: const Color(0xFF00C2FF),
            );
          }
          return GoogleFonts.montserrat(
            fontSize: 10,
            fontWeight: FontWeight.w500,
            color: Colors.white.withValues(alpha: 0.4),
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: Color(0xFF00C2FF), size: 24);
          }
          return IconThemeData(color: Colors.white.withValues(alpha: 0.4), size: 22);
        }),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF1E293B).withValues(alpha: 0.8),
        labelStyle: const TextStyle(color: Color(0xFF94A3B8)),
        floatingLabelStyle: const TextStyle(
          color: Color(0xFF00C2FF),
          fontSize: 12,
          fontWeight: FontWeight.w900,
          letterSpacing: 1.0,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFF00C2FF), width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Colors.redAccent, width: 1.5),
        ),
        errorStyle: const TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold),
        contentPadding: const EdgeInsets.fromLTRB(20, 24, 20, 16),
        alignLabelWithHint: true,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(double.infinity, 56),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          backgroundColor: const Color(0xFF00C2FF),
          foregroundColor: Colors.white,
          textStyle: GoogleFonts.montserrat(
            fontSize: 16,
            fontWeight: FontWeight.w700,
          ),
          elevation: 4,
          shadowColor: const Color(0xFF00C2FF).withValues(alpha: 0.4),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: Colors.white.withValues(alpha: 0.1),
        thickness: 1,
      ),
    );
  }
}
