Feature: Health Monitoring
  As a DevOps engineer
  I want to monitor my services health
  So that I can respond quickly to outages

  Background:
    Given the application is running
    And I am on the Monitors page

  Scenario: View monitors list
    Then I should see a list of configured monitors
    And each monitor should show its status (up/down/unknown)
    And each monitor should show last check time

  Scenario: Add a new monitor
    When I click "New Monitor" button
    And I enter "Production API" as name
    And I enter "https://api.example.com/health" as URL
    And I select 60 seconds check interval
    And I click "Add" button
    Then the monitor "Production API" should appear in the list
    And the monitor status should be "unknown"

  Scenario: Manual health check
    Given there is a monitor "Google" with URL "https://google.com"
    When I click "Check Now" on the monitor
    Then the monitor status should update
    And the response time should be displayed
    And a metrics entry should be recorded

  Scenario: Automatic incident creation on failure
    Given there is a monitor "Failing Service" with URL "http://localhost:9999"
    When the background health check runs
    And the monitor returns an error
    Then an incident should be automatically created
    And the incident severity should be "critical"
    And the monitor status should be "down"

  Scenario: Automatic incident resolution
    Given there is an open incident for monitor "Recovered Service"
    When the background health check runs
    And the monitor returns success
    Then the incident should be automatically resolved
    And the monitor status should be "up"
