import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../core/app_state.dart';
import '../models/assistant_reply.dart';
import '../models/task.dart';

class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key});

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final List<_ChatBubble> _messages = [
    const _ChatBubble(
      isUser: false,
      text:
          'Hi! I’m your RemindMe AI. I can help you schedule tasks instantly! 📋\n\nTry saying: "study tomorrow at 6 pm" or "gym on Friday at 8 am"',
    ),
  ];
  AssistantReply? _pendingTaskReply;
  bool _sending = false;

  bool _loadingHistory = true;

  @override
  void initState() {
    super.initState();
    _loadChatHistory();
  }

  Future<void> _loadChatHistory() async {
    final state = context.read<AppState>();
    try {
      final history = await state.api.getAssistantChatHistory();
      if (!mounted) return;
      setState(() {
        if (history.isNotEmpty) {
          _messages.clear();
          for (final msg in history) {
            _messages.add(_ChatBubble(
              isUser: msg['role'] == 'user',
              text: msg['content'] ?? '',
            ));
          }
        }
      });
    } catch (e) {
      debugPrint('Failed to load chat history: $e');
    } finally {
      if (mounted) {
        setState(() => _loadingHistory = false);
        _scrollToBottom();
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: Column(
        children: [
          // ── Messages ────────────────────────────────────────────
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 20),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                return _ChatBubbleWidget(msg: msg)
                    .animate()
                    .fadeIn(duration: 300.ms)
                    .slideY(begin: 0.05, end: 0, curve: Curves.easeOutQuad);
              },
            ),
          ),

          // ── Typing Indicator ───────────────────────────────────
          if (_sending)
            Padding(
              padding: const EdgeInsets.only(left: 20, bottom: 8),
              child: Row(
                children: [
                  const Text('AI is thinking', style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic)),
                  const SizedBox(width: 8),
                  const SizedBox(
                    width: 12,
                    height: 12,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ],
              ),
            ),

          // ── Pending Task Preview ───────────────────────────────
          if (_pendingTaskReply != null)
            _buildPendingCard(colors)
                .animate()
                .fadeIn()
                .slideY(begin: 0.5, end: 0, curve: Curves.easeOutBack),

          // ── Input Area ──────────────────────────────────────────
          _buildInputArea(colors),
        ],
      ),
    );
  }

  Widget _buildPendingCard(ColorScheme colors) {
    final task = _pendingTaskReply!.task;
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: colors.secondaryContainer.withValues(alpha: 0.9),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: colors.secondary.withValues(alpha: 0.3)),
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.1), blurRadius: 20, offset: const Offset(0, 8)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.auto_awesome_rounded, color: colors.secondary, size: 20),
              const SizedBox(width: 8),
              Text('QUICK SCHEDULER', style: GoogleFonts.montserrat(fontWeight: FontWeight.w800, fontSize: 12, letterSpacing: 1, color: colors.secondary)),
            ],
          ),
          const SizedBox(height: 12),
          Text(task['title'] ?? 'New Task', style: GoogleFonts.montserrat(fontWeight: FontWeight.w700, fontSize: 18)),
          const SizedBox(height: 6),
          Row(
            children: [
              Icon(Icons.calendar_today_rounded, size: 14, color: colors.onSecondaryContainer),
              const SizedBox(width: 6),
              Text('${task['date']} at ${task['time']}', style: const TextStyle(fontWeight: FontWeight.w500)),
            ],
          ),
          const SizedBox(height: 16),
          const Text('SET PRIORITY', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
          const SizedBox(height: 8),
          Row(
            children: [
              _PriorityBtn(label: 'Low', color: Colors.green, isSelected: task['priority']?.toString().toLowerCase() == 'low', onTap: () => _updateDraftPriority('Low')),
              const SizedBox(width: 8),
              _PriorityBtn(label: 'Med', color: Colors.orange, isSelected: task['priority']?.toString().toLowerCase() == 'medium', onTap: () => _updateDraftPriority('Medium')),
              const SizedBox(width: 8),
              _PriorityBtn(label: 'High', color: Colors.red, isSelected: task['priority']?.toString().toLowerCase() == 'high', onTap: () => _updateDraftPriority('High')),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: TextButton(
                  onPressed: () => setState(() => _pendingTaskReply = null),
                  child: const Text('Cancel'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton.icon(
                  onPressed: _savePendingTask,
                  icon: const Icon(Icons.check_rounded),
                  label: const Text('Save Task'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInputArea(ColorScheme colors) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      decoration: BoxDecoration(
        color: colors.surface,
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10, offset: const Offset(0, -4)),
        ],
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: () {
              context.read<AppState>().resetAssistantState();
              setState(() {
                _messages.clear();
                _messages.add(const _ChatBubble(
                  isUser: false,
                  text: 'Conversation reset. How can I help you now? 📋',
                ));
                _pendingTaskReply = null;
              });
            },
            icon: const Icon(Icons.refresh_rounded),
            color: colors.onSurfaceVariant.withValues(alpha: 0.5),
            tooltip: 'Reset',
          ),
          const SizedBox(width: 4),
          Expanded(
            child: TextField(
              controller: _controller,
              onSubmitted: (_) => _send(),
              decoration: InputDecoration(
                hintText: 'Type a reminder...',
                filled: true,
                fillColor: colors.surfaceContainerHighest.withValues(alpha: 0.5),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(28), borderSide: BorderSide.none),
                contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              ),
            ),
          ),
          const SizedBox(width: 10),
          IconButton.filled(
            onPressed: _sending ? null : _send,
            icon: Icon(_sending ? Icons.hourglass_empty_rounded : Icons.send_rounded),
            style: IconButton.styleFrom(
              minimumSize: const Size(50, 50),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            ),
          ).animate(onPlay: (c) => c.repeat(reverse: true))
           .shimmer(duration: 2000.ms, color: Colors.white24),
        ],
      ),
    );
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add(_ChatBubble(isUser: true, text: text));
      _controller.clear();
      _sending = true;
    });
    _scrollToBottom();

    final state = context.read<AppState>();
    try {
      final reply = await state.api.sendAssistantMessage(text);
      if (!mounted) return;
      setState(() {
        _messages.add(_ChatBubble(isUser: false, text: reply.response));
        _pendingTaskReply = reply.type == 'task' || reply.type == 'ready_to_save' ? reply : null;
      });
      
      if (reply.type == 'ready_to_save') {
        // Auto-save if everything is provided
        await _savePendingTask();
      } else if (reply.type == 'created') {
        await state.refreshAll();
      }
    } catch (e) {
      debugPrint('Assistant Error: $e');
      state.api.logError('Assistant UI Error: $e');
      if (!mounted) return;
      setState(() {
        _messages.add(_ChatBubble(isUser: false, text: 'Error: ${e.toString()}'));
      });
    } finally {
      if (mounted) {
        setState(() => _sending = false);
      }
      _scrollToBottom();
    }
  }

  Future<void> _savePendingTask() async {
    final task = _pendingTaskReply?.task;
    if (task == null) return;

    final title = task['title']?.toString() ?? '';
    final date = task['date']?.toString() ?? '';
    final time = task['time']?.toString() ?? '';
    final category = task['category']?.toString() ?? 'General';
    if (title.isEmpty || date.isEmpty || time.isEmpty) return;

    if (!mounted) return;
    await context.read<AppState>().createTask(
          TaskDraft(
            title: title,
            dueIso: DateTime.parse('${date}T$time:00').toUtc().toIso8601String(),
            priority: _priorityToInt(task['priority']?.toString()),
            category: category.isNotEmpty ? category : 'General',
          ),
        );

    if (!mounted) return;
    await context.read<AppState>().resetAssistantState();

    if (!mounted) return;
    setState(() {
      _pendingTaskReply = null;
      _messages.add(
        const _ChatBubble(
          isUser: false,
          text: 'Task saved! ✅',
        ),
      );
    });
    _scrollToBottom();
  }

  void _updateDraftPriority(String priority) {
    if (_pendingTaskReply == null) return;
    setState(() {
      final task = Map<String, dynamic>.from(_pendingTaskReply!.task);
      task['priority'] = priority;
      _pendingTaskReply = AssistantReply(
        type: _pendingTaskReply!.type,
        response: _pendingTaskReply!.response,
        task: task,
      );
    });
  }

  int _priorityToInt(String? value) {
    switch (value?.toLowerCase()) {
      case 'high': return 1;
      case 'medium': return 2;
      case 'low': return 3;
      default: return 2;
    }
  }
}

class _ChatBubble {
  const _ChatBubble({required this.isUser, required this.text});
  final bool isUser;
  final String text;
}

class _ChatBubbleWidget extends StatelessWidget {
  const _ChatBubbleWidget({required this.msg});
  final _ChatBubble msg;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Align(
      alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        margin: const EdgeInsets.only(bottom: 8),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: msg.isUser ? colors.primary : colors.surfaceContainerHighest,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(20),
            topRight: const Radius.circular(20),
            bottomLeft: Radius.circular(msg.isUser ? 20 : 4),
            bottomRight: Radius.circular(msg.isUser ? 4 : 20),
          ),
          boxShadow: [
            BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 4, offset: const Offset(0, 2)),
          ],
        ),
        child: Text(
          msg.text,
          style: TextStyle(
            color: msg.isUser ? Colors.white : colors.onSurface,
            fontSize: 15,
            height: 1.4,
          ),
        ),
      ),
    );
  }
}

class _PriorityBtn extends StatelessWidget {
  const _PriorityBtn({
    required this.label,
    required this.color,
    required this.isSelected,
    required this.onTap,
  });

  final String label;
  final Color color;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: isSelected ? color : color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: color.withValues(alpha: 0.3)),
          ),
          child: Center(
            child: Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.white : color,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
