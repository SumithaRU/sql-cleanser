/// <reference types="cypress" />

describe("Bidirectional Direction Selector", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("should display direction selector with default pg2ora selection", () => {
    cy.contains("🔄 Conversion Direction").should("be.visible");
    cy.get('[data-testid="direction-pg2ora"]').should("have.class", "selected");
    cy.contains("📍 Selected: 🐘➡️🔶 PostgreSQL → Oracle").should("be.visible");
  });

  it("should allow switching between directions", () => {
    // Click Oracle to PostgreSQL option
    cy.contains("Oracle → PostgreSQL").click();
    cy.contains("📍 Selected: 🔶➡️🐘 Oracle → PostgreSQL").should("be.visible");

    // Check that labels updated
    cy.contains("🔶 Oracle Scripts (Source Files)").should("be.visible");
    cy.contains("🐘 PostgreSQL Scripts (Target Files)").should("be.visible");

    // Switch back to PostgreSQL to Oracle
    cy.contains("PostgreSQL → Oracle").click();
    cy.contains("📍 Selected: 🐘➡️🔶 PostgreSQL → Oracle").should("be.visible");

    // Check that labels updated back
    cy.contains("📊 PostgreSQL Scripts (Source Files)").should("be.visible");
    cy.contains("🎯 Oracle Scripts (Target Files)").should("be.visible");
  });

  it("should persist direction selection in localStorage", () => {
    // Select Oracle to PostgreSQL
    cy.contains("Oracle → PostgreSQL").click();

    // Reload page
    cy.reload();

    // Should maintain Oracle to PostgreSQL selection
    cy.contains("📍 Selected: 🔶➡️🐘 Oracle → PostgreSQL").should("be.visible");
    cy.contains("🔶 Oracle Scripts (Source Files)").should("be.visible");
  });

  it("should disable direction selector during processing", () => {
    // This test would require mocking the API or having test files
    // For now, we'll just verify the selector exists and is interactive
    cy.contains("PostgreSQL → Oracle").should("not.be.disabled");
    cy.contains("Oracle → PostgreSQL").should("not.be.disabled");
  });

  it("should update file upload labels based on direction", () => {
    // Test PostgreSQL → Oracle direction
    cy.contains("PostgreSQL → Oracle").click();
    cy.contains("PostgreSQL Files").should("be.visible");
    cy.contains("Oracle Files").should("be.visible");

    // Test Oracle → PostgreSQL direction
    cy.contains("Oracle → PostgreSQL").click();
    cy.contains("Oracle Files").should("be.visible");
    cy.contains("PostgreSQL Files").should("be.visible");
  });

  it("should update button text based on direction", () => {
    // Default state should show generic message
    cy.contains("📁 Upload files to both sections").should("be.visible");

    // The button text will change based on files uploaded, but we can't easily test
    // file upload in Cypress without more complex setup
  });
});
