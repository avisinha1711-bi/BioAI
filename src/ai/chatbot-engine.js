/**
 * MOLGENOBOT AI Assistant
 * Advanced genetics chatbot with workflow capabilities
 */

class MolGenoBot {
    constructor() {
        this.knowledgeBase = new KnowledgeBase();
        this.nlpProcessor = new NLPProcessor();
        this.workflowManager = new WorkflowManager();
    }

    async processQuery(userMessage) {
        // 1. NLP processing
        const intent = this.nlpProcessor.detectIntent(userMessage);
        const entities = this.nlpProcessor.extractEntities(userMessage);
        
        // 2. Knowledge retrieval
        const response = this.knowledgeBase.getResponse(intent, entities);
        
        // 3. Workflow management
        if (this.workflowManager.isInWorkflow()) {
            return this.workflowManager.handleStep(userMessage);
        }
        
        return response;
    }

    startWorkflow(workflowType) {
        return this.workflowManager.startWorkflow(workflowType);
    }
}

export default MolGenoBot;
