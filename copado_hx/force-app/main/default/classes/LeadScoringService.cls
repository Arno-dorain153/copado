public with sharing class LeadScoringService {
    public static Integer calculateScore(Lead targetLead) {
        if (targetLead == null) return 0;
        Integer score = 0;
        if (targetLead.AnnualRevenue != null && targetLead.AnnualRevenue > 1000000) score += 50;
        if (targetLead.Industry == 'Technology') score += 35;
        return score;
    }
}
