import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class WarmupScreen extends StatefulWidget {
  const WarmupScreen({super.key});

  @override
  State<WarmupScreen> createState() => _WarmupScreenState();
}

class _WarmupScreenState extends State<WarmupScreen> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 0.85, end: 1.05).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: isDark
                ? [const Color(0xFF0F172A), const Color(0xFF1E293B)]
                : [const Color(0xFFF8FAFC), const Color(0xFFE2E8F0)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Stack(
            children: [
              // Decorative background glow
              Positioned(
                top: -150,
                right: -100,
                child: Container(
                  width: 300,
                  height: 300,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFF00C2FF).withValues(alpha: 0.12),
                  ),
                ),
              ),
              Positioned(
                bottom: -150,
                left: -100,
                child: Container(
                  width: 350,
                  height: 350,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFF6366F1).withValues(alpha: 0.1),
                  ),
                ),
              ),
              
              Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 32.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Pulsing Icon container
                      ScaleTransition(
                        scale: _pulseAnimation,
                        child: Container(
                          width: 90,
                          height: 90,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: const Color(0xFF00C2FF).withValues(alpha: 0.1),
                            border: Border.all(
                              color: const Color(0xFF00C2FF).withValues(alpha: 0.3),
                              width: 2,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF00C2FF).withValues(alpha: 0.2),
                                blurRadius: 20,
                                spreadRadius: 5,
                              )
                            ],
                          ),
                          child: const Icon(
                            Icons.cloud_sync_rounded,
                            size: 40,
                            color: Color(0xFF00C2FF),
                          ),
                        ),
                      ),
                      const SizedBox(height: 48),
                      
                      // Heading
                      Text(
                        'Connecting Secure Cloud',
                        textAlign: TextAlign.center,
                        style: GoogleFonts.montserrat(
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -0.5,
                          color: isDark ? Colors.white : const Color(0xFF0F172A),
                        ),
                      ),
                      const SizedBox(height: 16),
                      
                      // Explanation subtitle
                      Text(
                        'Warming up secure cloud database instance (Render Free Tier)... This may take up to 30 seconds to wake up the system. Thank you for your patience.',
                        textAlign: TextAlign.center,
                        style: GoogleFonts.inter(
                          fontSize: 14,
                          fontWeight: FontWeight.w400,
                          height: 1.5,
                          color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF475569),
                        ),
                      ),
                      const SizedBox(height: 48),
                      
                      // Circular indicator in custom styling
                      const SizedBox(
                        width: 48,
                        height: 48,
                        child: CircularProgressIndicator(
                          strokeWidth: 3.5,
                          valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00C2FF)),
                          backgroundColor: Colors.black12,
                        ),
                      ),
                      const SizedBox(height: 24),
                      
                      // Subtext
                      Text(
                        'Waiting for server response...',
                        style: GoogleFonts.inter(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 0.5,
                          color: const Color(0xFF00C2FF),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
