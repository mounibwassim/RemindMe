import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../core/app_state.dart';
// notification service not used on this screen; handled from AppState/home

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  // Track which sections have been expanded so we can lazy-load content
  final Map<String, bool> _loaded = {};

  void _markLoaded(String key) {
    if (!(_loaded[key] ?? false)) setState(() => _loaded[key] = true);
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Premium Security Status ─────────────────────────────────
          Container(
            margin: const EdgeInsets.only(bottom: 24),
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [
                  Color(0xFF10B981), // Emerald
                  Color(0xFF059669), // Darker Emerald
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF10B981).withValues(alpha: 0.2),
                  blurRadius: 20,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.2),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.verified_user_rounded,
                      color: Colors.white, size: 24),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Privacy Protected',
                        style: GoogleFonts.montserrat(
                          fontWeight: FontWeight.w800,
                          fontSize: 17,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Your data is end-to-end encrypted and stored securely on your device.',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.9),
                          fontSize: 12,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // ── Profile Section (Expandable) ─────────────────────────────
          _ExpandableSection(
            title: 'Profile',
            onExpand: () => _markLoaded('profile'),
            childrenBuilder: (ctx) => [
              _buildProfileHeader(state, colors, ctx),
              const SizedBox(height: 16),
              // Avatar gallery is lazy-loaded when the section is expanded
              if ((_loaded['profile'] ?? false))
                _buildAvatarGallery(state, colors),
            ],
          ),
          const SizedBox(height: 20),

          // ── App Settings (Expandable) ───────────────────────────────
          _ExpandableSection(
            title: 'App Settings',
            onExpand: () => _markLoaded('app'),
            childrenBuilder: (ctx) => [
              _buildSettingsGroup([
                _SettingTile(
                  icon: Icons.palette_outlined,
                  title: 'App Theme',
                  subtitle: 'Toggle Light / Dark',
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => state.toggleThemeMode(),
                ),
                _SettingTile(
                  icon: Icons.notifications_active_outlined,
                  title: 'Notification Permissions',
                  subtitle: state.isNotificationPermissionGranted
                      ? 'Status: Active and enabled'
                      : 'Status: Disabled (Tap to enable)',
                  trailing: Icon(
                    state.isNotificationPermissionGranted
                        ? Icons.check_circle_rounded
                        : Icons.error_outline_rounded,
                    color: state.isNotificationPermissionGranted
                        ? const Color(0xFF10B981)
                        : Colors.redAccent,
                    size: 20,
                  ),
                  onTap: () async {
                    if (!state.isNotificationPermissionGranted) {
                      _showInfoDialog(
                        ctx,
                        'Enable Notifications',
                        'RemindMe uses local scheduled alarms to alert you on task deadlines and custom schedules. Please grant permissions to activate notifications.',
                      );
                      await state.requestNotificationPermissions();
                    } else {
                      _showInfoDialog(
                        ctx,
                        'Notifications Active',
                        'System notifications and exact alarms are fully active and authorized.',
                      );
                    }
                  },
                ),
                _SettingTile(
                  icon: Icons.notifications_none_rounded,
                  title: 'Send Test Notification',
                  subtitle: 'Verify notification delivery & alerts',
                  trailing: const Icon(Icons.send_rounded),
                  onTap: () async {
                    await state.sendTestNotification();
                    ScaffoldMessenger.of(ctx).showSnackBar(
                      const SnackBar(content: Text('Test notification sent!')),
                    );
                  },
                ),
                _SettingTile(
                  icon: Icons.psychology_outlined,
                  title: 'AI Assistant Settings',
                  subtitle:
                      'Customize how your RemindMe Assistant helps organize and schedule your daily tasks.',
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => _showInfoDialog(ctx, 'AI Assistant Settings',
                      'Customize how your RemindMe Assistant helps organize and schedule your daily tasks.'),
                ),
                _SettingTile(
                  icon: Icons.dns_outlined,
                  title: 'Server Configuration',
                  subtitle: 'Endpoint: ${state.api.baseUrl}',
                  trailing: const Icon(Icons.edit_road_rounded),
                  onTap: () {
                    _showServerSettingsDialog(ctx, state);
                  },
                ),
              ], colors),
            ],
          ),
          const SizedBox(height: 20),

          // ── Privacy & Security (Expandable) ─────────────────────────
          _ExpandableSection(
            title: 'Privacy & Security',
            onExpand: () => _markLoaded('privacy'),
            childrenBuilder: (ctx) => [
              _buildSettingsGroup([
                _SettingTile(
                  icon: Icons.lock_outline_rounded,
                  title: 'Change Password',
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => _showChangePasswordDialog(ctx, state),
                ),
                _SettingTile(
                  icon: Icons.shield_outlined,
                  title: 'Privacy Policy',
                  subtitle:
                      'Your data is securely protected and used only to provide core RemindMe features.',
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => _showInfoDialog(ctx, 'Privacy Policy',
                      'Your data is securely protected and used only to provide core RemindMe features.'),
                ),
                _SettingTile(
                  icon: Icons.storage_rounded,
                  title: 'Secure Local Storage',
                  subtitle:
                      'Your tasks and personal information are stored securely on your device and synced safely with your account.',
                  trailing: const Icon(Icons.check_circle_rounded,
                      color: Color(0xFF10B981), size: 20),
                  onTap: () => _showInfoDialog(ctx, 'Secure Local Storage',
                      'Your tasks and personal information are stored securely on your device and synced safely with your account.'),
                ),
              ], colors),
            ],
          ),
          const SizedBox(height: 20),

          // ── Data Management (Expandable) ────────────────────────────
          _ExpandableSection(
            title: 'Data Management',
            onExpand: () => _markLoaded('data'),
            childrenBuilder: (ctx) => [
              _buildSettingsGroup([
                _SettingTile(
                  icon: Icons.cloud_upload_outlined,
                  title: 'Backup & Restore',
                  subtitle:
                      'Restore your tasks and preferences across devices using your secure account backup.',
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => _showInfoDialog(ctx, 'Backup & Restore',
                      'Restore your tasks and preferences across devices using your secure account backup.'),
                ),
                _SettingTile(
                  icon: Icons.delete_sweep_outlined,
                  title: 'Clear All Tasks',
                  titleColor: Colors.redAccent,
                  onTap: () => _showClearHistoryDialog(ctx, state),
                ),
              ], colors),
            ],
          ),
          const SizedBox(height: 20),

          // ── Support (Expandable) ───────────────────────────────────
          _ExpandableSection(
            title: 'Support',
            onExpand: () => _markLoaded('support'),
            childrenBuilder: (ctx) => [
              _buildSettingsGroup([
                _SettingTile(
                  icon: Icons.info_outline_rounded,
                  title: 'About RemindMe',
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => _showAboutDialog(ctx),
                ),
                _SettingTile(
                  icon: Icons.code_rounded,
                  title: 'App Version',
                  subtitle: 'Version 1.0.0\nBuild 2026.1',
                  onTap: () => _showInfoDialog(
                      ctx, 'App Version', 'Version 1.0.0\nBuild 2026.1'),
                ),
              ], colors),
            ],
          ),

          const SizedBox(height: 28),

          // ── Logout ───────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: OutlinedButton.icon(
              onPressed: () => _showLogoutDialog(context, state),
              icon: const Icon(Icons.logout_rounded),
              label: const Text('Sign Out'),
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.redAccent,
                side: const BorderSide(color: Colors.redAccent),
                padding: const EdgeInsets.all(16),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16)),
              ),
            ),
          ),
          const SizedBox(height: 48),
        ],
      ),
    );
  }

  Widget _buildProfileHeader(
      AppState state, ColorScheme colors, BuildContext context) {
    final hasAvatar =
        state.avatarEmoji != null && state.avatarEmoji!.isNotEmpty;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: colors.surfaceContainerHighest.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: colors.outlineVariant.withValues(alpha: 0.5)),
      ),
      child: Row(
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [colors.primary, colors.tertiary],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: colors.primary.withValues(alpha: 0.2),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Center(
              child: hasAvatar &&
                      state.avatarEmoji != null &&
                      state.avatarEmoji!.isNotEmpty
                  ? (state.avatarEmoji!.contains('avatars/')
                      ? ClipRRect(
                          borderRadius: BorderRadius.circular(32),
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
                  : Text(
                      (state.displayName ?? state.username ?? 'U')
                          .substring(0, 1)
                          .toUpperCase(),
                      style: GoogleFonts.montserrat(
                        fontWeight: FontWeight.w800,
                        fontSize: 24,
                        color: Colors.white,
                      ),
                    ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  state.displayName ?? state.username ?? 'User',
                  style: GoogleFonts.montserrat(
                    fontWeight: FontWeight.w700,
                    fontSize: 18,
                  ),
                ),
                Text(
                  state.email ?? 'Standard Account',
                  style: TextStyle(
                    color: colors.onSurfaceVariant,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                    content: Text(
                        'Profile editing is coming in v2.2! Use Avatar Gallery below.')),
              );
            },
            icon: const Icon(Icons.edit_rounded, size: 20),
            style: IconButton.styleFrom(
              backgroundColor: colors.primary.withValues(alpha: 0.1),
              foregroundColor: colors.primary,
            ),
          ),
          const SizedBox(width: 6),
          IconButton(
            onPressed: () async {
              final confirm = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('Clear Profile Image'),
                  content: const Text(
                      'Clear your profile image and revert to initials?'),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(ctx, false),
                        child: const Text('Cancel')),
                    FilledButton(
                        onPressed: () => Navigator.pop(ctx, true),
                        child: const Text('Clear')),
                  ],
                ),
              );
              if (confirm == true) {
                await state.updateAvatar('');
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Profile image cleared')));
                }
              }
            },
            icon: const Icon(Icons.delete_outline, size: 20),
            style: IconButton.styleFrom(
              backgroundColor: colors.surfaceVariant.withValues(alpha: 0.06),
              foregroundColor: colors.onSurface,
            ),
            tooltip: 'Clear Image',
          ),
        ],
      ),
    );
  }

  Widget _buildAvatarGallery(AppState state, ColorScheme colors) {
    final emojis = [
      '🚀',
      '🎯',
      '🔥',
      '💎',
      '⚡',
      '🌟',
      '🍀',
      '🍎',
      '🐯',
      '🦊',
      '🐱',
      '🐶',
      '🐼',
      '🐨',
      '🦁',
      '🦉',
      '🎮',
      '👾',
      '🕹️',
      '💻',
      '🖥️',
      '⌨️',
      '🖱️',
      '🎧',
      '💼',
      '👔',
      '📁',
      '📅',
      '📝',
      '📌',
      '📈',
      '✅',
      '🎨',
      '🎬',
      '🎭',
      '🎸',
      '🎹',
      '🎻',
      '🎧',
      '🎤',
      '🏠',
      '🚲',
      '🚗',
      '✈️',
      '🏝️',
      '🏔️',
      '⛺',
      '🌇',
    ];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surfaceContainerHighest.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: colors.outlineVariant.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 4),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 6,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
            ),
            itemCount: emojis.length,
            itemBuilder: (context, index) {
              final emoji = emojis[index];
              final isSelected = state.avatarEmoji == emoji;
              return InkWell(
                onTap: () => state.updateAvatar(emoji),
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  decoration: BoxDecoration(
                    color: isSelected
                        ? colors.primary.withValues(alpha: 0.15)
                        : colors.surface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: isSelected
                          ? colors.primary
                          : colors.outlineVariant.withValues(alpha: 0.3),
                      width: isSelected ? 2 : 1,
                    ),
                    boxShadow: isSelected
                        ? [
                            BoxShadow(
                              color: colors.primary.withValues(alpha: 0.2),
                              blurRadius: 8,
                              offset: const Offset(0, 2),
                            )
                          ]
                        : null,
                  ),
                  child: Center(
                    child: Text(
                      emoji,
                      style: const TextStyle(fontSize: 24),
                    ),
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsGroup(List<Widget> children, ColorScheme colors) {
    return Container(
      decoration: BoxDecoration(
        color: colors.surfaceContainerHighest.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: colors.outlineVariant.withValues(alpha: 0.5)),
      ),
      child: Column(children: children),
    );
  }

  void _showClearHistoryDialog(BuildContext context, AppState state) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Clear All Tasks'),
        content: const Text(
            'Are you sure you want to delete ALL tasks (including pending)? This cannot be undone.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () async {
              try {
                await state.clearAllHistory();
                Navigator.pop(ctx);
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('All tasks cleared')));
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error clearing history: $e')));
                }
              }
            },
            style: FilledButton.styleFrom(backgroundColor: Colors.redAccent),
            child: const Text('Clear All'),
          ),
        ],
      ),
    );
  }

  void _showLogoutDialog(BuildContext context, AppState state) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Sign Out'),
        content:
            const Text('Are you sure you want to sign out of your account?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              state.signOut();
              Navigator.pop(ctx);
            },
            child: const Text('Sign Out'),
          ),
        ],
      ),
    );
  }

  void _showChangePasswordDialog(BuildContext context, AppState state) {
    showDialog(
      context: context,
      builder: (ctx) => const _ChangePasswordDialog(),
    );
  }

  void _showInfoDialog(BuildContext context, String title, String content) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Got it')),
        ],
      ),
    );
  }

  void _showLogsDialog(BuildContext context, String logs) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('System Logs'),
        content: SizedBox(
          width: double.maxFinite,
          child: SingleChildScrollView(
            child: Text(
              logs,
              style: const TextStyle(fontFamily: 'monospace', fontSize: 10),
            ),
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Close')),
        ],
      ),
    );
  }

  void _showAboutDialog(BuildContext context) {
    showAboutDialog(
      context: context,
      applicationName: 'RemindMe',
      applicationVersion: '1.0.0 Build 2026.1',
      applicationIcon:
          const Icon(Icons.alarm_rounded, size: 48, color: Colors.blue),
      children: [
        const Text(
          'RemindMe is a smart productivity assistant designed to help users organize tasks, schedules, and daily routines efficiently.',
        ),
        const SizedBox(height: 12),
        const Text(
            'App mission: Help users get more done with less effort using thoughtful automation.'),
        const SizedBox(height: 8),
        const Text('Developer: RemindMe Inc. — contact@remindme.example'),
        const SizedBox(height: 8),
        const Text(
            'Features: Smart suggestions, AI-driven scheduling, cross-device backup, and a private-by-default design.'),
        const SizedBox(height: 12),
        const Text('© 2026 RemindMe Inc.'),
      ],
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
                controller.text = 'https://api-remindme.onrender.com';
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

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: Text(
        title.toUpperCase(),
        style: GoogleFonts.montserrat(
          fontSize: 11,
          fontWeight: FontWeight.w800,
          color: Theme.of(context).colorScheme.primary,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}

class _SettingTile extends StatelessWidget {
  const _SettingTile({
    required this.icon,
    required this.title,
    this.subtitle,
    this.trailing,
    this.titleColor,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final Color? titleColor;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(24),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: (titleColor ?? colors.primary).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: titleColor ?? colors.primary, size: 20),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                      color: titleColor ?? colors.onSurface,
                    ),
                  ),
                  if (subtitle != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      subtitle!,
                      style: TextStyle(
                        fontSize: 12,
                        color: colors.onSurfaceVariant.withValues(alpha: 0.7),
                      ),
                    ),
                  ],
                ],
              ),
            ),
            if (trailing != null) trailing!,
          ],
        ),
      ),
    );
  }
}

class _ExpandableSection extends StatefulWidget {
  const _ExpandableSection({
    required this.title,
    required this.childrenBuilder,
    this.onExpand,
    super.key,
  });

  final String title;
  final VoidCallback? onExpand;
  final List<Widget> Function(BuildContext) childrenBuilder;

  @override
  State<_ExpandableSection> createState() => _ExpandableSectionState();
}

class _ExpandableSectionState extends State<_ExpandableSection> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 6),
      decoration: BoxDecoration(
        color: colors.surfaceContainerHighest.withValues(alpha: 0.02),
        borderRadius: BorderRadius.circular(16),
      ),
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        childrenPadding:
            const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        onExpansionChanged: (v) {
          setState(() => _expanded = v);
          if (v && widget.onExpand != null) widget.onExpand!();
        },
        title: Text(widget.title,
            style: GoogleFonts.montserrat(fontWeight: FontWeight.w700)),
        trailing: Icon(
            _expanded ? Icons.expand_less_rounded : Icons.expand_more_rounded),
        children: widget.childrenBuilder(context),
      ),
    );
  }
}

class _ChangePasswordDialog extends StatefulWidget {
  const _ChangePasswordDialog();

  @override
  State<_ChangePasswordDialog> createState() => _ChangePasswordDialogState();
}

class _ChangePasswordDialogState extends State<_ChangePasswordDialog> {
  final currentCtrl = TextEditingController();
  final newCtrl = TextEditingController();
  final confirmCtrl = TextEditingController();
  bool _obscurePassword = true;

  @override
  void initState() {
    super.initState();
    currentCtrl.addListener(() => setState(() {}));
    newCtrl.addListener(() => setState(() {}));
    confirmCtrl.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    currentCtrl.dispose();
    newCtrl.dispose();
    confirmCtrl.dispose();
    super.dispose();
  }

  bool get _isPasswordLengthInvalid => newCtrl.text.isNotEmpty && newCtrl.text.length < 8;
  bool get _isConfirmInvalid => confirmCtrl.text.isNotEmpty && newCtrl.text != confirmCtrl.text;
  bool get _isValid => currentCtrl.text.isNotEmpty && newCtrl.text.length >= 8 && newCtrl.text == confirmCtrl.text;

  Future<void> _handleUpdate(AppState state) async {
    try {
      await state.changePassword(currentCtrl.text, newCtrl.text);
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Password updated successfully.'),
            backgroundColor: Colors.green,
          ),
        );
        state.signOut();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final colors = Theme.of(context).colorScheme;

    return AlertDialog(
      title: const Text('Secure Password Change'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Verify your identity to update security.',
              style: TextStyle(fontSize: 12, color: Colors.grey)),
          const SizedBox(height: 16),
          TextField(
            controller: currentCtrl,
            obscureText: _obscurePassword,
            decoration: InputDecoration(
              labelText: 'Current Password',
              floatingLabelBehavior: FloatingLabelBehavior.always,
              prefixIcon: const Icon(Icons.lock_person_outlined),
              suffixIcon: IconButton(
                icon: Icon(_obscurePassword ? Icons.visibility : Icons.visibility_off),
                onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
              ),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: newCtrl,
            obscureText: _obscurePassword,
            decoration: const InputDecoration(
              labelText: 'New Password',
              floatingLabelBehavior: FloatingLabelBehavior.always,
              prefixIcon: Icon(Icons.lock_outline),
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
          const SizedBox(height: 12),
          TextField(
            controller: confirmCtrl,
            obscureText: _obscurePassword,
            decoration: const InputDecoration(
              labelText: 'Confirm New Password',
              floatingLabelBehavior: FloatingLabelBehavior.always,
              prefixIcon: Icon(Icons.check_circle_outline),
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
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(
          onPressed: (!_isValid || state.isLoading) ? null : () => _handleUpdate(state),
          child: state.isLoading
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Text('Update Security'),
        ),
      ],
    );
  }
}

