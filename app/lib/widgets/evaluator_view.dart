import 'package:flutter/material.dart';
import '../models/idea.dart';
import '../theme/app_theme.dart';

/// Renders the evaluation JSON for all 9 categories.
class EvaluatorView extends StatelessWidget {
  final Idea idea;
  const EvaluatorView({super.key, required this.idea});

  @override
  Widget build(BuildContext context) {
    final ev = idea.eval;
    if (ev.isEmpty) {
      if (idea.status == 'processing') return const _Processing();
      return const _Empty();
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _Header(ev: ev),
        const SizedBox(height: 16),
        ..._buildSections(ev),
        _ScoreCards(scores: Map<String, dynamic>.from(ev['scores'] ?? {})),
        _AnalystTake(text: ev['analyst_take'] as String?),
        _Summary(text: (ev['final_summary'] ?? ev['closing']) as String?),
        _Learning(learn: ev['learning'] as Map<String, dynamic>?),
        const SizedBox(height: 40),
      ],
    );
  }

  List<Widget> _buildSections(Map<String, dynamic> ev) {
    final cat = ev['category'] as String? ?? '';
    switch (cat) {
      case 'Business':    return _businessSections(ev);
      case 'Technology':  return _techSections(ev);
      case 'Engineering': return _engSections(ev);
      case 'Science':     return _sciSections(ev);
      case 'Mathematics': return _mathSections(ev);
      case 'Society':     return _societySections(ev);
      case 'Philosophy':  return _philSections(ev);
      case 'Personal':    return _personalSections(ev);
      case 'Other':       return _otherSections(ev);
      default:            return _generalSections(ev);
    }
  }

  List<Widget> _businessSections(Map ev) => [
    _Section('Market Context', _kvMap(ev['market_context'])),
    _Section('Competitive Landscape', _kvMap(ev['competitive_landscape'])),
    _Section('Unit Economics', _kvMap(ev['unit_economics'])),
    _Section('Weakest Links', _kvMap(ev['weakest_links'])),
    _Section('Idea Positioning', _kvMap(ev['idea_positioning'])),
  ];

  List<Widget> _techSections(Map ev) => [
    _Section('Problem Space', _kvMap(ev['problem_space'])),
    _Section('Technical Assessment', _kvMap(ev['technical_assessment'])),
    _Section('Product Strategy', _kvMap(ev['product_strategy'])),
    _Section('Competitive Landscape', _kvMap(ev['competitive_landscape'])),
  ];

  List<Widget> _engSections(Map ev) {
    final hook = ev['hook'] as String?;
    final core = ev['core'] as String?;
    final sections = (ev['sections'] as List? ?? []);
    return [
      if (hook != null && hook.isNotEmpty) _Section('Hook', [_Field(label: '', value: hook)]),
      if (core != null && core.isNotEmpty) _Section('Core Mechanism', [_Field(label: '', value: core)]),
      ...sections.map<Widget>((s) {
        final title = s['title'] as String? ?? '';
        final content = s['content'] as String? ?? '';
        return _Section(title, [_Field(label: '', value: content)]);
      }),
    ];
  }

  List<Widget> _sciSections(Map ev) {
    final hook = ev['hook'] as String?;
    final core = ev['core'] as String?;
    final sections = (ev['sections'] as List? ?? []);
    return [
      if (hook != null && hook.isNotEmpty) _Section('Hook', [_Field(label: '', value: hook)]),
      if (core != null && core.isNotEmpty) _Section('Core Mechanism', [_Field(label: '', value: core)]),
      ...sections.map<Widget>((s) {
        final title = s['title'] as String? ?? '';
        final content = s['content'] as String? ?? '';
        return _Section(title, [_Field(label: '', value: content)]);
      }),
    ];
  }

  List<Widget> _mathSections(Map ev) => [
    _Section('Conjecture', _kvMap(ev['conjecture'])),
    _Section('Prior Art', _kvMap(ev['prior_art'])),
    _Section('Proof Strategy', _kvMap(ev['proof_strategy'])),
    _Section('Counterexample Risks', _listSection(ev['counterexample_risks'])),
    _Section('India Mathematics Context', _kvMap(ev['india_mathematics_context'])),
  ];

  List<Widget> _societySections(Map ev) => [
    _Section('Hypothesis', _kvMap(ev['hypothesis'])),
    _Section('Prior Art', _kvMap(ev['prior_art'])),
    _Section('Evidence & Method', _kvMap(ev['evidence_and_method'])),
    _Section('Confounds & Risks', _kvMap(ev['confounds_and_risks'])),
    _Section('India Social Context', _kvMap(ev['india_social_context'])),
  ];

  List<Widget> _philSections(Map ev) => [
    _Section('Argument', _kvMap(ev['argument'])),
    _Section('Prior Art', _kvMap(ev['prior_art'])),
    _Section('Argument Analysis', _kvMap(ev['argument_analysis'])),
    _Section('India Philosophy Context', _kvMap(ev['india_philosophy_context'])),
  ];

  List<Widget> _personalSections(Map ev) => [
    _Section('Core Claim', _kvMap(ev['core_claim'])),
    _Section('Evidence Base', _kvMap(ev['evidence_base'])),
    _Section('Implementation', _kvMap(ev['implementation'])),
    _Section('India Context', _kvMap(ev['india_context'])),
  ];

  List<Widget> _otherSections(Map ev) => [
    _Section('Core Analysis', _kvMap(ev['core_analysis'])),
    _Section('Prior Context', _kvMap(ev['prior_context'])),
    _Section('Feasibility', _kvMap(ev['feasibility'])),
    _Section('India Relevance', _kvMap(ev['india_relevance'])),
  ];

  List<Widget> _generalSections(Map ev) => [
    _Section('Core Analysis', _kvMap(ev['core_analysis'])),
  ];

  // ── Helpers ───────────────────────────────────────────────

  static List<Widget> _kvMap(dynamic val) {
    if (val == null) return [const _EmptyField()];
    if (val is String) return [_Field(label: '', value: val)];
    if (val is Map) {
      return val.entries
          .where((e) => e.value != null && e.value.toString().isNotEmpty)
          .map((e) {
        final label = _labelify(e.key.toString());
        final v = e.value;
        if (v is List) return _BulletField(label: label, items: v);
        return _Field(label: label, value: v.toString());
      }).toList();
    }
    return [_Field(label: '', value: val.toString())];
  }

  static List<Widget> _listSection(dynamic val) {
    if (val == null) return [const _EmptyField()];
    if (val is List) {
      return val.map((item) {
        if (item is Map) {
          final text = item.values
              .where((v) => v is String && v.isNotEmpty)
              .join(' — ');
          return _BulletItem(text: text);
        }
        return _BulletItem(text: item.toString());
      }).toList();
    }
    return [_Field(label: '', value: val.toString())];
  }

  static String _labelify(String key) =>
      key.replaceAll('_', ' ').split(' ').map((w) =>
          w.isEmpty ? '' : w[0].toUpperCase() + w.substring(1)).join(' ');
}

// ── Sub-widgets ───────────────────────────────────────────────

class _Processing extends StatelessWidget {
  const _Processing();
  @override Widget build(BuildContext context) => const Center(
    child: Padding(
      padding: EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 36, height: 36,
            child: CircularProgressIndicator(color: AppColors.amber, strokeWidth: 2),
          ),
          SizedBox(height: 20),
          Text(
            'Processing…',
            style: TextStyle(color: AppColors.amber, fontSize: 14),
          ),
          SizedBox(height: 8),
          Text(
            'Engine is working on your idea.\nCome back in a moment.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textDim, fontSize: 12, height: 1.6),
          ),
        ],
      ),
    ),
  );
}

class _Empty extends StatelessWidget {
  const _Empty();
  @override Widget build(BuildContext context) => const Center(
    child: Padding(
      padding: EdgeInsets.all(32),
      child: Text(
        'No evaluation yet.\nTap Analyze in the Note tab.',
        textAlign: TextAlign.center,
        style: TextStyle(color: AppColors.textDim, fontSize: 14, height: 1.6),
      ),
    ),
  );
}

class _Header extends StatelessWidget {
  final Map<String, dynamic> ev;
  const _Header({required this.ev});

  @override Widget build(BuildContext context) {
    final title = ev['idea_summary']      as String?
               ?? ev['conjecture_summary'] as String?
               ?? ev['hypothesis_summary'] as String?
               ?? ev['argument_summary']   as String?
               ?? ev['observation_summary']as String?
               ?? ev['hook']               as String?
               ?? '';
    final cls = ev['final_classification'] as String? ?? '';
    final cat = ev['category'] as String? ?? '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (cat.isNotEmpty)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: AppColors.amberDim,
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(cat, style: const TextStyle(
              color: AppColors.amber, fontSize: 11, fontWeight: FontWeight.w500,
            )),
          ),
        if (title.isNotEmpty) ...[
          const SizedBox(height: 10),
          Text(title, style: const TextStyle(
            color: AppColors.text, fontSize: 16,
            fontWeight: FontWeight.w600, height: 1.4,
          )),
        ],
        if (cls.isNotEmpty) ...[
          const SizedBox(height: 8),
          _ClassBadge(cls: cls),
        ],
      ],
    );
  }
}

class _ClassBadge extends StatelessWidget {
  final String cls;
  const _ClassBadge({required this.cls});

  @override Widget build(BuildContext context) {
    final c = cls.toLowerCase();
    Color bg; Color fg;
    if (c.contains('breakthrough') || c.contains('paradigm') || c.contains('exceptional')) {
      bg = const Color(0x1A9C6ADE); fg = const Color(0xFF9C6ADE);
    } else if (c.contains('promising') || c.contains('tractable') || c.contains('worth')) {
      bg = AppColors.amberDim; fg = AppColors.amber;
    } else if (c.contains('weak') || c.contains('trivially') || c.contains('counterproductive')) {
      bg = AppColors.redDim; fg = AppColors.red;
    } else {
      bg = AppColors.greenDim; fg = AppColors.green;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(6)),
      child: Text(cls, style: TextStyle(color: fg, fontSize: 12, fontWeight: FontWeight.w500)),
    );
  }
}

class _Section extends StatelessWidget {
  final String       label;
  final List<Widget> children;
  const _Section(this.label, this.children);

  @override Widget build(BuildContext context) {
    if (children.isEmpty || children.every((w) => w is _EmptyField)) {
      return const SizedBox.shrink();
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label.toUpperCase(), style: const TextStyle(
            color: AppColors.amber, fontSize: 10,
            fontWeight: FontWeight.w600, letterSpacing: 1.0,
          )),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.border, width: 0.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: children,
            ),
          ),
        ],
      ),
    );
  }
}

class _Field extends StatelessWidget {
  final String label;
  final String value;
  const _Field({required this.label, required this.value});

  @override Widget build(BuildContext context) {
    if (value.isEmpty || value == 'null') return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (label.isNotEmpty) ...[
            Text(label, style: const TextStyle(
              color: AppColors.textDim, fontSize: 11, fontWeight: FontWeight.w500,
            )),
            const SizedBox(height: 3),
          ],
          Text(value, style: const TextStyle(
            color: AppColors.text, fontSize: 13, height: 1.55,
          )),
        ],
      ),
    );
  }
}

class _BulletField extends StatelessWidget {
  final String     label;
  final List<dynamic> items;
  const _BulletField({required this.label, required this.items});

  @override Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (label.isNotEmpty) ...[
            Text(label, style: const TextStyle(
              color: AppColors.textDim, fontSize: 11, fontWeight: FontWeight.w500,
            )),
            const SizedBox(height: 4),
          ],
          ...items.map((item) {
            final text = item is Map
                ? item.values.where((v) => v is String && v.isNotEmpty).join(' — ')
                : item.toString();
            return _BulletItem(text: text);
          }),
        ],
      ),
    );
  }
}

class _BulletItem extends StatelessWidget {
  final String text;
  const _BulletItem({required this.text});

  @override Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 4),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.only(top: 6, right: 8),
          child: CircleAvatar(
            radius: 2.5,
            backgroundColor: AppColors.textDim,
          ),
        ),
        Expanded(child: Text(text, style: const TextStyle(
          color: AppColors.textMuted, fontSize: 13, height: 1.5,
        ))),
      ],
    ),
  );
}

class _EmptyField extends StatelessWidget {
  const _EmptyField();
  @override Widget build(BuildContext context) => const SizedBox.shrink();
}

class _ScoreCards extends StatelessWidget {
  final Map<String, dynamic> scores;
  const _ScoreCards({required this.scores});

  @override Widget build(BuildContext context) {
    final entries = scores.entries
        .where((e) => e.value != null && e.value.toString().isNotEmpty)
        .toList();
    if (entries.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('SCORES', style: TextStyle(
            color: AppColors.amber, fontSize: 10,
            fontWeight: FontWeight.w600, letterSpacing: 1.0,
          )),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8, runSpacing: 8,
            children: entries.map((e) {
              final label = e.key.replaceAll('_', ' ').split(' ')
                  .map((w) => w.isEmpty ? '' : w[0].toUpperCase() + w.substring(1))
                  .join(' ');
              final val = e.value;
              final isNum = val is num;
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.border, width: 0.5),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(label, style: const TextStyle(
                      color: AppColors.textDim, fontSize: 10,
                    )),
                    const SizedBox(height: 4),
                    isNum
                        ? RichText(text: TextSpan(children: [
                            TextSpan(text: val.toString(), style: const TextStyle(
                              color: AppColors.amber, fontSize: 20,
                              fontWeight: FontWeight.w600,
                            )),
                            const TextSpan(text: '/10', style: TextStyle(
                              color: AppColors.textDim, fontSize: 12,
                            )),
                          ]))
                        : Text(val.toString(), style: const TextStyle(
                            color: AppColors.textMuted, fontSize: 12,
                          )),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

class _AnalystTake extends StatelessWidget {
  final String? text;
  const _AnalystTake({this.text});

  @override Widget build(BuildContext context) {
    if (text == null || text!.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('ANALYST TAKE', style: TextStyle(
            color: AppColors.amber, fontSize: 10,
            fontWeight: FontWeight.w600, letterSpacing: 1.0,
          )),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.border2, width: 0.5),
            ),
            child: Text(
              '"$text"',
              style: const TextStyle(
                color: AppColors.text,
                fontSize: 14,
                fontStyle: FontStyle.italic,
                height: 1.7,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Summary extends StatelessWidget {
  final String? text;
  const _Summary({this.text});

  @override Widget build(BuildContext context) {
    if (text == null || text!.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('FINAL SUMMARY', style: TextStyle(
            color: AppColors.amber, fontSize: 10,
            fontWeight: FontWeight.w600, letterSpacing: 1.0,
          )),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.border, width: 0.5),
            ),
            child: Text(text!, style: const TextStyle(
              color: AppColors.text, fontSize: 14, height: 1.6,
            )),
          ),
        ],
      ),
    );
  }
}

class _Learning extends StatelessWidget {
  final Map<String, dynamic>? learn;
  const _Learning({this.learn});

  @override Widget build(BuildContext context) {
    if (learn == null) return const SizedBox.shrink();
    final queries = List<String>.from(learn!['search_queries'] ?? []);
    final sources = List<dynamic>.from(learn!['cited_sources'] ?? []);
    if (queries.isEmpty && sources.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('LEARNING', style: TextStyle(
            color: AppColors.amber, fontSize: 10,
            fontWeight: FontWeight.w600, letterSpacing: 1.0,
          )),
          const SizedBox(height: 8),
          if (queries.isNotEmpty) ...[
            const Text('Search Queries', style: TextStyle(
              color: AppColors.textDim, fontSize: 11,
            )),
            const SizedBox(height: 6),
            Wrap(
              spacing: 6, runSpacing: 6,
              children: queries.map((q) => Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: AppColors.amberDim,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.amber.withOpacity(0.3)),
                ),
                child: Text(q, style: const TextStyle(
                  color: AppColors.amber, fontSize: 12,
                )),
              )).toList(),
            ),
            const SizedBox(height: 12),
          ],
          if (sources.isNotEmpty) ...[
            const Text('Cited Sources', style: TextStyle(
              color: AppColors.textDim, fontSize: 11,
            )),
            const SizedBox(height: 6),
            ...sources.map((s) {
              final src = s is Map ? s : <String, dynamic>{};
              final idx   = src['index']?.toString() ?? '';
              final title = src['title'] as String? ?? '—';
              return Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: RichText(text: TextSpan(children: [
                  TextSpan(text: '[$idx] ', style: const TextStyle(
                    color: AppColors.amber, fontSize: 12,
                    fontWeight: FontWeight.w600,
                  )),
                  TextSpan(text: title, style: const TextStyle(
                    color: AppColors.textMuted, fontSize: 12, height: 1.4,
                  )),
                ])),
              );
            }),
          ],
        ],
      ),
    );
  }
}
