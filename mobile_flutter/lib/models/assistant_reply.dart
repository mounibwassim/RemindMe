class AssistantReply {
  const AssistantReply({
    required this.type,
    required this.response,
    required this.task,
  });

  final String type;
  final String response;
  final Map<String, dynamic> task;

  factory AssistantReply.fromJson(Map<String, dynamic> json) {
    return AssistantReply(
      type: json['type'] as String? ?? 'chat',
      response: json['response'] as String? ?? '',
      task: Map<String, dynamic>.from(json['task'] as Map? ?? {}),
    );
  }
}
