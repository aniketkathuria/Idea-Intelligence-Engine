import 'dart:convert';

class Cluster {
  final int?   id;
  final String? superIdea;
  final String? mergeReasoning;
  final List<int> ideaIds;
  final DateTime createdAt;

  const Cluster({
    this.id,
    this.superIdea,
    this.mergeReasoning,
    required this.ideaIds,
    required this.createdAt,
  });

  Cluster copyWith({
    int?    id,
    String? superIdea,
    String? mergeReasoning,
    List<int>? ideaIds,
    DateTime?  createdAt,
  }) => Cluster(
    id:             id             ?? this.id,
    superIdea:      superIdea      ?? this.superIdea,
    mergeReasoning: mergeReasoning ?? this.mergeReasoning,
    ideaIds:        ideaIds        ?? this.ideaIds,
    createdAt:      createdAt      ?? this.createdAt,
  );

  Map<String, dynamic> toMap() => {
    if (id != null) 'id': id,
    'super_idea':       superIdea,
    'merge_reasoning':  mergeReasoning,
    'idea_ids_json':    jsonEncode(ideaIds),
    'created_at':       createdAt.millisecondsSinceEpoch,
  };

  factory Cluster.fromMap(Map<String, dynamic> m) => Cluster(
    id:             m['id'] as int?,
    superIdea:      m['super_idea']      as String?,
    mergeReasoning: m['merge_reasoning'] as String?,
    ideaIds: List<int>.from(
        (jsonDecode(m['idea_ids_json'] as String) as List).map((e) => e as int)),
    createdAt: DateTime.fromMillisecondsSinceEpoch(m['created_at'] as int),
  );
}
