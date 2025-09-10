const express = require('express');
const cors = require('cors');
const path = require('path');
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Genetic code mapping
const geneticCode = {
    "UUU": "Phe", "UUC": "Phe", "UUA": "Leu", "UUG": "Leu",
    "CUU": "Leu", "CUC": "Leu", "CUA": "Leu", "CUG": "Leu",
    "AUU": "Ile", "AUC": "Ile", "AUA": "Ile", "AUG": "Met",
    "GUU": "Val", "GUC": "Val", "GUA": "Val", "GUG": "Val",
    "UCU": "Ser", "UCC": "Ser", "UCA": "Ser", "UCG": "Ser",
    "CCU": "Pro", "CCC": "Pro", "CCA": "Pro", "CCG": "Pro",
    "ACU": "Thr", "ACC": "Thr", "ACA": "Thr", "ACG": "Thr",
    "GCU": "Ala", "GCC": "Ala", "GCA": "Ala", "GCG": "Ala",
    "UAU": "Tyr", "UAC": "Tyr", "UAA": "STOP", "UAG": "STOP",
    "CAU": "His", "CAC": "His", "CAA": "Gln", "CAG": "Gln",
    "AAU": "Asn", "AAC": "Asn", "AAA": "Lys", "AAG": "Lys",
    "GAU": "Asp", "GAC": "Asp", "GAA": "Glu", "GAG": "Glu",
    "UGU": "Cys", "UGC": "Cys", "UGA": "STOP", "UGG": "Trp",
    "CGU": "Arg", "CGC": "Arg", "CGA": "Arg", "CGG": "Arg",
    "AGU": "Ser", "AGC": "Ser", "AGA": "Arg", "AGG": "Arg",
    "GGU": "Gly", "GGC": "Gly", "GGA": "Gly", "GGG": "Gly"
};

// Function to get complementary DNA strand
function getComplementaryDNA(sequence) {
    const complementMap = { 'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C' };
    return sequence.split('').map(base => complementMap[base]).join('');
}

// Function to transcribe DNA to mRNA
function transcribeToMRNA(sequence) {
    const transcriptionMap = { 'A': 'U', 'T': 'A', 'C': 'G', 'G': 'C' };
    return sequence.split('').map(base => transcriptionMap[base]).join('');
}

// Function to translate mRNA to polypeptide
function translateToPolypeptide(mRNA) {
    let polypeptide = [];
    
    // Split mRNA into codons (groups of 3 nucleotides)
    for (let i = 0; i < mRNA.length; i += 3) {
        const codon = mRNA.substring(i, i + 3);
        
        // Stop translation if we encounter a stop codon
        if (codon.length < 3) break;
        
        const aminoAcid = geneticCode[codon];
        if (aminoAcid === "STOP") {
            polypeptide.push("STOP");
            break;
        }
        
        polypeptide.push(aminoAcid);
    }
    
    return polypeptide.join('-');
}

// API endpoint for translation
app.post('/translate', (req, res) => {
    try {
        const { sequence } = req.body;
        
        // Validate input
        if (!sequence || typeof sequence !== 'string') {
            return res.status(400).json({ error: 'Invalid sequence provided' });
        }
        
        if (!/^[ATCG]+$/i.test(sequence)) {
            return res.status(400).json({ error: 'Sequence can only contain A, T, C, or G' });
        }
        
        const upperSequence = sequence.toUpperCase();
        
        // Get complementary DNA (5' to 3')
        const complementaryDNA = getComplementaryDNA(upperSequence);
        
        // Transcribe to mRNA (5' to 3')
        const mRNA = transcribeToMRNA(complementaryDNA);
        
        // Translate to polypeptide chain
        const polypeptide = translateToPolypeptide(mRNA);
        
        res.json({
            templateDNA: upperSequence,
            complementaryDNA: complementaryDNA,
            mRNA: mRNA,
            polypeptide: polypeptide
        });
        
    } catch (error) {
        console.error('Translation error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Serve the frontend
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
app.listen(port, () => {
    console.log(`Genetic translator server running at http://localhost:${port}`);
});
