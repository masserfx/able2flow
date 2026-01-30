Feature: Kanban Board
  As a user
  I want to manage tasks on a kanban board
  So that I can track my work progress

  Background:
    Given the application is running
    And I am on the Board page

  Scenario: View kanban columns
    Then I should see 4 columns
    And the columns should be "Backlog", "To Do", "In Progress", "Done"

  Scenario: Create a new task
    When I click "New Task" button
    And I enter "Implement feature X" as title
    And I select "To Do" column
    And I click "Add Task"
    Then the task "Implement feature X" should appear in "To Do" column

  Scenario: Move task between columns
    Given there is a task "Test task" in "To Do" column
    When I drag the task to "In Progress" column
    Then the task should appear in "In Progress" column
    And the task should not appear in "To Do" column
    And an audit log entry should be created with action "move"

  Scenario: Complete a task
    Given there is a task "Finish report" in "In Progress" column
    When I check the completed checkbox
    Then the task should be marked as completed
    And the task title should have strikethrough style

  Scenario: Delete a task
    Given there is a task "Old task" in "Backlog" column
    When I click the delete button on the task
    And I confirm the deletion
    Then the task should be removed from the board
    And an audit log entry should be created with action "delete"
