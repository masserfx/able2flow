Feature: Incident Management
  As an on-call engineer
  I want to manage incidents
  So that I can track and resolve issues efficiently

  Background:
    Given the application is running
    And I am on the Incidents page

  Scenario: Create manual incident
    When I click "Report Incident" button
    And I enter "Database connection timeout" as title
    And I select "critical" severity
    And I click "Report" button
    Then the incident should appear in the list
    And the incident status should be "open"
    And the incident severity should be "critical"

  Scenario: Acknowledge incident
    Given there is an open incident "Server CPU high"
    When I click "Acknowledge" button on the incident
    Then the incident status should change to "acknowledged"
    And the acknowledged timestamp should be recorded
    And an audit log entry should be created

  Scenario: Resolve incident
    Given there is an acknowledged incident "Memory leak"
    When I click "Resolve" button on the incident
    Then the incident status should change to "resolved"
    And the resolved timestamp should be recorded
    And an audit log entry should be created

  Scenario: Filter incidents by status
    Given there are incidents with different statuses
    When I click "Open" filter tab
    Then I should only see incidents with status "open" or "acknowledged"
    When I click "Resolved" filter tab
    Then I should only see incidents with status "resolved"
    When I click "All" filter tab
    Then I should see all incidents

  Scenario: View incident duration
    Given there is an incident that started 2 hours ago
    Then the incident should show duration "2h 0m"
    When the incident is resolved
    Then the duration should be the time between start and resolution
