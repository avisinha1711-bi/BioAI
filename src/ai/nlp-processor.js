/**
 * Natural Language Processor
 * Enhanced understanding of genetics questions
 */

class NLPProcessor {
    detectIntent(message) {
        const intents = {
            'definition': /(what is|define|explain)/i,
            'process': /(how does|how do|process)/i,
            'comparison': /(difference between|compare|vs)/i,
            'workflow': /(guide me|step by step|workflow)/i
        };

        for (const [intent, pattern] of Object.entries(intents)) {
            if (pattern.test(message)) return intent;
        }
        return 'general';
    }

    extractEntities(message) {
        const geneticsTerms = [
            'dna', 'rna', 'protein', 'gene', 'chromosome',
            'mutation', 'transcription', 'translation', 'replication'
        ];

        return geneticsTerms.filter(term => 
            message.toLowerCase().includes(term)
        );
    }

    calculateSimilarity(query, topic) {
        // Semantic similarity calculation
        // Handle synonyms and related terms
    }
}

export default NLPProcessor;
