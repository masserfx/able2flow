Feature: Audit Log
  As an administrator
  I want to see all system changes
  So that I can audit actions and recover from mistakes

  Background:
    Given the application is running

  Scenario: Log task creation
    When I create a task with title "New feature"
    Then an audit log entry should be created
    And the entry should have entity_type "task"
    And the entry should have action "create"
    And the entry should have new_value containing the task data
    And the entry should have old_value as null

  Scenario: Log task update with old and new values
    Given there is a task with title "Original title"
    When I update the task title to "Updated title"
    Then an audit log entry should be created
    And the entry should have action "update"
    And the entry old_value should contain "Original title"
    And the entry new_value should contain "Updated title"

  Scenario: Log task deletion
    Given there is a task with title "To be deleted"
    When I delete the task
    Then an audit log entry should be created
    And the entry should have action "delete"
    And the entry should have old_value containing the deleted task data
    And the entry should have new_value as null

  Scenario: Log incident workflow
    Given there is an incident "Test incident"
    When I acknowledge the incident
    Then an audit log entry with action "acknowledge" should be created
    When I resolve the incident
    Then an audit log entry with action "resolve" should be created

  Scenario: View audit log timeline
    Given there are multiple audit log entries
    When I navigate to the Audit page
    Then I should see entries sorted by timestamp descending
    And each entry should show the action type with color coding
    And each entry should show relative time (e.g., "5m ago")

  Scenario: Disaster recovery from audit log
    Given there is an audit log entry for a deleted task
    Then the old_value should contain all task fields
    And an administrator could use this data to restore the task
