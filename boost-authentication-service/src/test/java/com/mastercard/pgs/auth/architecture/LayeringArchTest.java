package com.mastercard.pgs.auth.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;

/**
 * Layering governance, blocking in {@code mvn verify}.
 *
 * <p>HTTP concerns do not reach across the service layer to the legacy edge: the API layer
 * must never depend on the legacy client package.
 */
@AnalyzeClasses(packages = "com.mastercard.pgs.auth",
        importOptions = ImportOption.DoNotIncludeTests.class)
class LayeringArchTest {

    @ArchTest
    static final ArchRule apiMustNotDependOnLegacyClient =
            noClasses().that().resideInAPackage("..api..")
                    .should().dependOnClassesThat().resideInAPackage("..client..");
}
