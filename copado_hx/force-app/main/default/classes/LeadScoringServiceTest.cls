@isTest
private class LeadScoringServiceTest {
    @isTest
    static void testCalculateScore() {
        Lead myLead = new Lead(
            LastName = 'Test',
            Company = 'Test Co',
            AnnualRevenue = 2000000,
            Industry = 'Technology'
        );
        Integer score = LeadScoringService.calculateScore(myLead);
        System.assertEquals(85, score);
    }
}
