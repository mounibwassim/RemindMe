import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../core/app_state.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();

  // Sign In fields
  final _username = TextEditingController();
  final _password = TextEditingController();

  late final TabController _tabController;
  final _signupFormKey = GlobalKey<FormState>();
  bool _obscurePassword = true;
  bool _obscureSignupPassword = true;
  // Sign Up fields
  final _displayName = TextEditingController();
  final _signupEmail = TextEditingController();
  final _signupPassword = TextEditingController();
  final _confirmPassword = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    _displayName.dispose();
    _signupEmail.dispose();
    _signupPassword.dispose();
    _confirmPassword.dispose();
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: colors.surface,
      body: Stack(
        children: [
          // ── Futuristic Background ─────────────────────────────────
          const _FuturisticBackground(),

          Positioned(
            top: 16,
            right: 16,
            child: SafeArea(
              child: ClipOval(
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
                  child: Container(
                    color: Colors.white.withOpacity(0.08),
                    child: IconButton(
                      icon: const Icon(Icons.dns_outlined, color: Colors.white70),
                      tooltip: 'Server Settings',
                      onPressed: () => _showServerSettingsDialog(context, state),
                    ),
                  ),
                ),
              ),
            ),
          ),

          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 440),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // ── Logo / Branding ───────────────────────────────────
                      Hero(
                        tag: 'logo',
                        child: _buildLogo(colors),
                      ).animate().fadeIn(duration: 800.ms).scale(delay: 200.ms),
                      const SizedBox(height: 16),
                      Text(
                        'RemindMe',
                        style: GoogleFonts.montserrat(
                          fontSize: 40,
                          fontWeight: FontWeight.w800,
                          color: colors.onSurface,
                          letterSpacing: -1,
                        ),
                      )
                          .animate()
                          .fadeIn(delay: 400.ms)
                          .slideY(begin: 0.2, end: 0),
                      const SizedBox(height: 4),
                      Text(
                        'SECURE • ENCRYPTED • INTELLIGENT',
                        style: GoogleFonts.montserrat(
                          color: const Color(0xFF38BDF8),
                          letterSpacing: 3,
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                        ),
                      ).animate().fadeIn(delay: 600.ms),
                      const SizedBox(height: 40),

                      // ── Glassmorphic Login Card ───────────────────────
                      ClipRRect(
                        borderRadius: BorderRadius.circular(32),
                        child: BackdropFilter(
                          filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
                          child: Container(
                            padding: const EdgeInsets.all(32),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.03),
                              borderRadius: BorderRadius.circular(32),
                              border: Border.all(
                                color: Colors.white.withValues(alpha: 0.08),
                                width: 1.5,
                              ),
                              gradient: LinearGradient(
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                                colors: [
                                  Colors.white.withValues(alpha: 0.05),
                                  Colors.white.withValues(alpha: 0.01),
                                ],
                              ),
                            ),
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                // Main auth UI
                                ...[
                                  Container(
                                    padding: const EdgeInsets.all(4),
                                    decoration: BoxDecoration(
                                      color:
                                          Colors.black.withValues(alpha: 0.2),
                                      borderRadius: BorderRadius.circular(16),
                                    ),
                                    child: TabBar(
                                      controller: _tabController,
                                      indicatorSize: TabBarIndicatorSize.tab,
                                      dividerColor: Colors.transparent,
                                      indicator: BoxDecoration(
                                        color: const Color(0xFF00C2FF),
                                        borderRadius: BorderRadius.circular(12),
                                        boxShadow: [
                                          BoxShadow(
                                            color: const Color(0xFF00C2FF)
                                                .withValues(alpha: 0.3),
                                            blurRadius: 10,
                                            offset: const Offset(0, 4),
                                          ),
                                        ],
                                      ),
                                      labelColor: Colors.white,
                                      unselectedLabelColor:
                                          Colors.white.withValues(alpha: 0.5),
                                      labelStyle: GoogleFonts.montserrat(
                                        fontWeight: FontWeight.w700,
                                        fontSize: 13,
                                      ),
                                      tabs: const [
                                        Tab(text: 'Sign In'),
                                        Tab(text: 'Sign Up'),
                                      ],
                                    ),
                                  ),
                                  const SizedBox(height: 32),
                                  ListenableBuilder(
                                    listenable: _tabController,
                                    builder: (context, _) {
                                      return AnimatedContainer(
                                        duration:
                                            const Duration(milliseconds: 300),
                                        curve: Curves.easeInOut,
                                        height: _tabController.index == 0
                                            ? 280
                                            : 400,
                                        child: TabBarView(
                                          controller: _tabController,
                                          children: [
                                            _buildSignInForm(state, colors),
                                            _buildSignUpForm(state, colors),
                                          ],
                                        ),
                                      );
                                    },
                                  ),
                                ],
                                // developer mode removed for production
                              ],
                            ),
                          ),
                        ),
                      ).animate().fadeIn(delay: 800.ms),

                      const SizedBox(height: 24),
                      TextButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                                builder: (context) =>
                                    const _ForgotPasswordScreen()),
                          );
                        },
                        child: Text(
                          'Forgot Password?',
                          style: GoogleFonts.montserrat(
                            color: colors.primary.withValues(alpha: 0.8),
                            fontWeight: FontWeight.w600,
                            fontSize: 13,
                          ),
                        ),
                      ),

                      // ── Error Message ─────────────────────────────────────
                      if (state.errorMessage != null) ...[
                        const SizedBox(height: 24),
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.redAccent.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                                color: Colors.redAccent.withValues(alpha: 0.2)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.error_outline_rounded,
                                  color: Colors.redAccent, size: 20),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  state.errorMessage!,
                                  style: const TextStyle(
                                      color: Colors.redAccent, fontSize: 13),
                                ),
                              ),
                            ],
                          ),
                        ).animate().shake(),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLogo(ColorScheme colors) {
    return Container(
      width: 100,
      height: 100,
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.1),
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white.withValues(alpha: 0.2)),
      ),
      child: Container(
        decoration: BoxDecoration(
          color: Theme.of(context).brightness == Brightness.dark
              ? const Color(0xFF0F172A)
              : Colors.white,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: colors.primary.withValues(alpha: 0.1),
              blurRadius: 10,
              spreadRadius: 2,
            ),
          ],
        ),
        clipBehavior: Clip.antiAlias,
        child: Image.asset(
          'assets/logo.png',
          errorBuilder: (context, error, stackTrace) => const Icon(
            Icons.lock_clock_rounded,
            color: Color(0xFF00C2FF),
            size: 50,
          ),
        ),
      ),
    );
  }

  Widget _buildSignInForm(AppState state, ColorScheme colors) {
    return SingleChildScrollView(
      physics:
          const BouncingScrollPhysics(), // Allow scrolling if content overflows card
      child: Form(
        key: _formKey,
        child: Column(
          children: [
            TextFormField(
              controller: _username,
              style: TextStyle(color: colors.onSurface, fontSize: 15),
              decoration: const InputDecoration(
                labelText: 'Username',
                prefixIcon: Icon(Icons.person_outline, size: 20),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Required';
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _password,
              obscureText: _obscurePassword,
              style: TextStyle(color: colors.onSurface, fontSize: 15),
              decoration: InputDecoration(
                labelText: 'Password',
                prefixIcon: const Icon(Icons.lock_outlined, size: 20),
                suffixIcon: IconButton(
                  icon: Icon(
                    _obscurePassword
                        ? Icons.visibility_outlined
                        : Icons.visibility_off_outlined,
                    size: 20,
                  ),
                  onPressed: () =>
                      setState(() => _obscurePassword = !_obscurePassword),
                ),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Required';
                return null;
              },
            ),
            const SizedBox(height: 32),
            FilledButton(
              onPressed: state.isLoading ? null : _handleSignIn,
              child: state.isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Text('Sign In'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSignUpForm(AppState state, ColorScheme colors) {
    return SingleChildScrollView(
      physics:
          const BouncingScrollPhysics(), // Allow scrolling if content overflows card
      child: Form(
        key: _signupFormKey,
        child: Column(
          children: [
            TextFormField(
              controller: _displayName,
              decoration: const InputDecoration(
                labelText: 'Username',
                prefixIcon: Icon(Icons.person_outlined),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Username is required';
                if (v.length < 2) return 'Username must be at least 2 characters';
                return null;
              },
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _signupEmail,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(
                labelText: 'Email',
                prefixIcon: Icon(Icons.email_outlined),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Email is required';
                if (!v.contains('@') || !v.contains('.')) {
                  return 'Enter a valid email';
                }
                return null;
              },
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _signupPassword,
              obscureText: _obscureSignupPassword,
              decoration: InputDecoration(
                labelText: 'Password',
                prefixIcon: const Icon(Icons.lock_outlined),
                suffixIcon: IconButton(
                  icon: Icon(
                    _obscureSignupPassword
                        ? Icons.visibility_outlined
                        : Icons.visibility_off_outlined,
                  ),
                  onPressed: () => setState(
                      () => _obscureSignupPassword = !_obscureSignupPassword),
                ),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Password is required';
                if (v.length < 8)
                  return 'Password must be at least 8 characters';
                return null;
              },
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _confirmPassword,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Confirm Password',
                prefixIcon: Icon(Icons.lock_outlined),
              ),
              validator: (v) {
                if (v == null || v.isEmpty)
                  return 'Please confirm your password';
                if (v != _signupPassword.text) return 'Passwords do not match';
                return null;
              },
            ),
            const SizedBox(height: 20),
            FilledButton(
              onPressed: state.isLoading ? null : _handleSignUp,
              child: state.isLoading
                  ? const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: Colors.white,
                      ),
                    )
                  : const Text('Create Account'),
            ),
          ],
        ),
      ),
    );
  }

  String? _required(String? value) {
    if (value == null || value.trim().isEmpty) return 'Required';
    return null;
  }

  Future<void> _handleSignIn() async {
    if (!_formKey.currentState!.validate()) return;
    await context.read<AppState>().firebaseSignIn(
          _username.text.trim(),
          _password.text,
        );
  }

  Future<void> _handleSignUp() async {
    if (!_signupFormKey.currentState!.validate()) return;
    await context.read<AppState>().firebaseSignUp(
          _signupEmail.text.trim(),
          _signupPassword.text,
          _displayName.text.trim(),
        );
  }

  void _showServerSettingsDialog(BuildContext context, AppState state) {
    final controller = TextEditingController(text: state.api.baseUrl);
    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('Server Configuration'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Enter the backend base URL. Change this to connect to localhost, an emulator, or your custom cloud server.',
                style: TextStyle(fontSize: 13),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: controller,
                style: const TextStyle(fontSize: 14),
                decoration: const InputDecoration(
                  labelText: 'API Base URL',
                  hintText: 'https://example.onrender.com or http://10.0.2.2:8000',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                controller.text = 'https://remindme-backend-k9mb.onrender.com';
              },
              child: const Text('Default Render'),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
              },
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final url = controller.text.trim();
                if (url.isNotEmpty) {
                  await state.changeApiBaseUrl(url);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('API URL updated to: $url')),
                    );
                    Navigator.pop(ctx);
                  }
                }
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }
}

// ── Forgot Password Screen (embedded) ─────────────────────────────────────

class _ForgotPasswordScreen extends StatefulWidget {
  const _ForgotPasswordScreen();

  @override
  State<_ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<_ForgotPasswordScreen> {
  final _username = TextEditingController();
  bool _sent = false;
  bool _completed = false;

  @override
  void dispose() {
    _username.dispose();
    super.dispose();
  }

  Future<void> _sendReset() async {
    final state = context.read<AppState>();
    final input = _username.text.trim();
    if (input.isEmpty) {
      setState(() {});
      return;
    }

    try {
      await state.forgotPassword(input);
      setState(() {
        _sent = true;
      });
    } catch (e) {
      // Error is surfaced via state.errorMessage and UI, but backend ensures this rarely throws
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Reset Password')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.lock_reset, size: 64, color: colors.primary),
                  const SizedBox(height: 16),
                  Text(
                    'Recover your account',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Enter your username or registered email.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: colors.onSurfaceVariant,
                        ),
                  ),
                  const SizedBox(height: 28),
                  if (_completed) ...[
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: Colors.green.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Column(
                        children: [
                          const Icon(Icons.check_circle,
                              color: Colors.green, size: 48),
                          const SizedBox(height: 12),
                          const Text(
                            'Password reset successfully',
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 18,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'You can now sign in with your new password.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: colors.onSurfaceVariant),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Back to Sign In'),
                    ),
                  ] else if (!_sent) ...[
                    if (state.errorMessage != null) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: colors.errorContainer.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                              color: colors.error.withValues(alpha: 0.3)),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.error_outline,
                                color: colors.error, size: 20),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                state.errorMessage!,
                                style: TextStyle(
                                  color: colors.error,
                                  fontSize: 13,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ).animate().shake(),
                      const SizedBox(height: 16),
                    ],
                    TextFormField(
                      controller: _username,
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.done,
                      onFieldSubmitted: (_) => _sendReset(),
                      decoration: const InputDecoration(
                        labelText: 'Username or registered email',
                        prefixIcon: Icon(Icons.person_outline),
                      ),
                    ),
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: state.isLoading ? null : _sendReset,
                      child: state.isLoading
                          ? const SizedBox(
                              width: 22,
                              height: 22,
                              child: CircularProgressIndicator(
                                strokeWidth: 2.5,
                                color: Colors.white,
                              ),
                            )
                          : const Text('Send Recovery Code'),
                    ),
                  ] else ...[
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: colors.primaryContainer.withValues(alpha: 0.3),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Column(
                        children: [
                          Icon(Icons.mark_email_read_outlined,
                              size: 48, color: colors.primary),
                          const SizedBox(height: 12),
                          const Text(
                            'Check Your Inbox',
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 18,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'If the account exists, a recovery email has been sent. Please check your spam folder if you do not see it within a few minutes.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: colors.onSurfaceVariant),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: FilledButton(
                            onPressed: () => Navigator.pop(context),
                            child: const Text('Back to Sign In'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        OutlinedButton(
                          onPressed: () {
                            showModalBottomSheet(
                              context: context,
                              isScrollControlled: true,
                              backgroundColor: Colors.transparent,
                              builder: (context) => Container(
                                height: MediaQuery.of(context).size.height * 0.85,
                                decoration: BoxDecoration(
                                  color: colors.surface,
                                  borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
                                ),
                                child: _ResetPasswordScreen(email: state.email ?? _username.text.trim()),
                              ),
                            );
                          },
                          child: const Text('Enter Code'),
                        ),
                      ],
                    ),
                  ],
                  if (state.errorMessage != null && !_completed) ...[
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: colors.primary.withValues(alpha: 0.06),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        state.errorMessage!,
                        textAlign: TextAlign.center,
                        style: TextStyle(color: colors.onSurfaceVariant),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _FuturisticBackground extends StatelessWidget {
  const _FuturisticBackground({super.key});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: Theme.of(context).brightness == Brightness.dark
                  ? const [
                      Color(0xFF020617),
                      Color(0xFF0F172A),
                      Color(0xFF1E293B),
                    ]
                  : const [
                      Color(0xFFF8FAFC),
                      Color(0xFFF1F5F9),
                      Color(0xFFE2E8F0),
                    ],
              stops: const [0.0, 0.5, 1.0],
            ),
          ),
        ),
        const _AmbientGlow(
          top: -100,
          right: -50,
          color: Color(0xFF00C2FF),
          size: 400,
          opacity: 0.12,
        ),
        const _AmbientGlow(
          bottom: -50,
          left: -100,
          color: Color(0xFF38BDF8),
          size: 500,
          opacity: 0.08,
        ),
        const _AmbientGlow(
          top: 200,
          left: -150,
          color: Color(0xFF0EA5E9),
          size: 300,
          opacity: 0.05,
        ),
        _ParticleField(color: Theme.of(context).colorScheme.onSurface),
      ],
    );
  }
}

class _AmbientGlow extends StatelessWidget {
  const _AmbientGlow({
    required this.color,
    required this.size,
    required this.opacity,
    this.top,
    this.left,
    this.right,
    this.bottom,
  });

  final Color color;
  final double size;
  final double opacity;
  final double? top, left, right, bottom;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: top,
      left: left,
      right: right,
      bottom: bottom,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: color.withValues(alpha: opacity),
              blurRadius: size * 0.6,
              spreadRadius: size * 0.1,
            ),
          ],
        ),
      ),
    );
  }
}

class _ParticleField extends StatefulWidget {
  const _ParticleField({required this.color});
  final Color color;

  @override
  State<_ParticleField> createState() => _ParticleFieldState();
}

class _ParticleFieldState extends State<_ParticleField>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller =
        AnimationController(vsync: this, duration: const Duration(seconds: 10))
          ..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return CustomPaint(
          size: Size.infinite,
          painter: _ParticlePainter(_controller.value, widget.color),
        );
      },
    );
  }
}

class _ParticlePainter extends CustomPainter {
  _ParticlePainter(this.progress, this.color);
  final double progress;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = color.withValues(alpha: 0.1);

    // Very subtle floating particles
    for (var i = 0; i < 20; i++) {
      final x = (size.width * (i * 0.13 + progress * 0.1)) % size.width;
      final y = (size.height * (i * 0.21 - progress * 0.05)) % size.height;
      canvas.drawCircle(Offset(x, y), 1.5, paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class _ResetPasswordScreen extends StatefulWidget {
  const _ResetPasswordScreen({required this.email});
  final String email;

  @override
  State<_ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends State<_ResetPasswordScreen> {
  final _code = TextEditingController();
  final _password = TextEditingController();
  final _confirmPassword = TextEditingController();
  bool _obscurePassword = true;

  @override
  void initState() {
    super.initState();
    _code.addListener(() => setState(() {}));
    _password.addListener(() => setState(() {}));
    _confirmPassword.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _code.dispose();
    _password.dispose();
    _confirmPassword.dispose();
    super.dispose();
  }

  bool get _isPasswordLengthInvalid => _password.text.isNotEmpty && _password.text.length < 8;
  bool get _isConfirmInvalid => _confirmPassword.text.isNotEmpty && _password.text != _confirmPassword.text;
  bool get _isValid => _code.text.length == 6 && _password.text.length >= 8 && _password.text == _confirmPassword.text;

  Future<void> _handleReset() async {
    final state = context.read<AppState>();
    try {
      await state.confirmPasswordReset(
        _code.text.trim(),
        _password.text,
        email: widget.email,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Password updated successfully.'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.popUntil(context, (route) => route.isFirst);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Reset failed: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final colors = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.vpn_key_outlined, size: 64, color: colors.primary),
          const SizedBox(height: 16),
          Text(
            'Reset Password',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Enter the 6-digit recovery code and your new password.',
            textAlign: TextAlign.center,
            style: TextStyle(color: colors.onSurfaceVariant),
          ),
          const SizedBox(height: 28),
          TextFormField(
            controller: _code,
            keyboardType: TextInputType.number,
            maxLength: 6,
            decoration: const InputDecoration(
              labelText: 'Recovery Code (6-digit)',
              prefixIcon: Icon(Icons.pin_outlined),
              counterText: '',
            ),
          ),
          const SizedBox(height: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _password,
                obscureText: _obscurePassword,
                decoration: InputDecoration(
                  labelText: 'New Password',
                  prefixIcon: const Icon(Icons.lock_outline),
                  suffixIcon: IconButton(
                    icon: Icon(_obscurePassword ? Icons.visibility : Icons.visibility_off),
                    onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                  ),
                ),
              ),
              if (_isPasswordLengthInvalid)
                Padding(
                  padding: const EdgeInsets.only(top: 6, left: 12),
                  child: Text(
                    'Password must contain at least 8 characters.',
                    style: TextStyle(color: colors.error, fontSize: 12, fontWeight: FontWeight.w500),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _confirmPassword,
                obscureText: _obscurePassword,
                decoration: const InputDecoration(
                  labelText: 'Confirm New Password',
                  prefixIcon: Icon(Icons.lock_outline),
                ),
              ),
              if (_isConfirmInvalid)
                Padding(
                  padding: const EdgeInsets.only(top: 6, left: 12),
                  child: Text(
                    'Passwords do not match.',
                    style: TextStyle(color: colors.error, fontSize: 12, fontWeight: FontWeight.w500),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: (!_isValid || state.isLoading) ? null : _handleReset,
              child: state.isLoading
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Save New Password'),
            ),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
        ],
      ),
    );
  }

  void _showServerSettingsDialog(BuildContext context, AppState state) {
    final controller = TextEditingController(text: state.api.baseUrl);
    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('Server Configuration'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Enter the backend base URL. Change this to connect to localhost, an emulator, or your custom cloud server.',
                style: TextStyle(fontSize: 13),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: controller,
                style: const TextStyle(fontSize: 14),
                decoration: const InputDecoration(
                  labelText: 'API Base URL',
                  hintText: 'https://example.onrender.com or http://10.0.2.2:8000',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                controller.text = 'https://remindme-backend-k9mb.onrender.com';
              },
              child: const Text('Default Render'),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
              },
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final url = controller.text.trim();
                if (url.isNotEmpty) {
                  await state.changeApiBaseUrl(url);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('API URL updated to: $url')),
                    );
                    Navigator.pop(ctx);
                  }
                }
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }
}
