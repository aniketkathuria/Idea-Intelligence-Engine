import 'dart:convert';

class Idea {
  final int?    id;
  final String  rawIdea;
  final String  status;       // draft | processing | completed | failed
  final String? category;
  final Map<String, dynamic>? evaluation;
  final List<dynamic>?        research;
  final List<double>?         embedding;
  final Map<String, dynamic>? synthesis;
  final int?    clusterId;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Idea({
    this.id,
    required this.rawIdea,
    this.status    = 'draft',
    this.category,
    this.evaluation,
    this.research,
    this.embedding,
    this.synthesis,
    this.clusterId,
    required this.createdAt,
    required this.updatedAt,
  });

  // Title: first non-empty line of rawIdea, trimmed, max 60 chars
  String get title {
    final first = rawIdea.split('\n').map((l) => l.trim()).firstWhere(
      (l) => l.isNotEmpty,
      orElse: () => 'Untitled',
    );
    return first.length > 60 ? '${first.substring(0, 60)}…' : first;
  }

  String get preview {
    final clean = rawIdea.trim();
    return clean.length > 120 ? '${clean.substring(0, 120)}…' : clean;
  }

  bool get isAnalyzed  => status == 'completed';
  bool get isProcessing => status == 'processing';
  bool get isDraft     => status == 'draft';
  bool get isFailed    => status == 'failed';

  // Convenience: pull the evaluation sub-map
  Map<String, dynamic> get eval => evaluation ?? {};

  Idea copyWith({
    int?    id,
    String? rawIdea,
    String? status,
    String? category,
    Map<String, dynamic>? evaluation,
    List<dynamic>?        research,
    List<double>?         embedding,
    Map<String, dynamic>? synthesis,
    int?    clusterId,
    DateTime? createdAt,
    DateTime? updatedAt,
    bool clearCluster = false,
  }) => Idea(
    id:         id         ?? this.id,
    rawIdea:    rawIdea    ?? this.rawIdea,
    status:     status     ?? this.status,
    category:   category   ?? this.category,
    evaluation: evaluation ?? this.evaluation,
    research:   research   ?? this.research,
    embedding:  embedding  ?? this.embedding,
    synthesis:  synthesis  ?? this.synthesis,
    clusterId:  clearCluster ? null : (clusterId ?? this.clusterId),
    createdAt:  createdAt  ?? this.createdAt,
    updatedAt:  updatedAt  ?? this.updatedAt,
  );

  Map<String, dynamic> toMap() => {
    if (id != null) 'id': id,
    'raw_idea':        rawIdea,
    'status':          status,
    'category':        category,
    'evaluation_json': evaluation != null ? jsonEncode(evaluation) : null,
    'research_json':   research   != null ? jsonEncode(research)   : null,
    'embedding_json':  embedding  != null ? jsonEncode(embedding)  : null,
    'synthesis_json':  synthesis  != null ? jsonEncode(synthesis)  : null,
    'cluster_id':      clusterId,
    'created_at':      createdAt.millisecondsSinceEpoch,
    'updated_at':      updatedAt.millisecondsSinceEpoch,
  };

  factory Idea.fromMap(Map<String, dynamic> m) => Idea(
    id:         m['id'] as int?,
    rawIdea:    m['raw_idea'] as String,
    status:     m['status']   as String? ?? 'draft',
    category:   m['category'] as String?,
    evaluation: m['evaluation_json'] != null
        ? Map<String, dynamic>.from(jsonDecode(m['evaluation_json'] as String))
        : null,
    research: m['research_json'] != null
        ? List<dynamic>.from(jsonDecode(m['research_json'] as String))
        : null,
    embedding: m['embedding_json'] != null
        ? List<double>.from(
            (jsonDecode(m['embedding_json'] as String) as List).map((e) => (e as num).toDouble()))
        : null,
    synthesis: m['synthesis_json'] != null
        ? Map<String, dynamic>.from(jsonDecode(m['synthesis_json'] as String))
        : null,
    clusterId:  m['cluster_id'] as int?,
    createdAt:  DateTime.fromMillisecondsSinceEpoch(m['created_at'] as int),
    updatedAt:  DateTime.fromMillisecondsSinceEpoch(m['updated_at'] as int),
  );

  // Shape expected by /process-idea past_ideas list
  Map<String, dynamic> toApiShape() => {
    'id':        id,
    'raw_idea':  rawIdea,
    'embedding': embedding ?? [],
    'analysis':  {'evaluation': evaluation ?? {}, 'research': research ?? []},
    'cluster_id': clusterId,
    'synthesis':  synthesis,
  };
}
