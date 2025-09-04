import type { ResourceData } from "@/arches_modular_reports/ModularReport/types.ts";

import type { WidgetDirtyStates } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/types.ts";

function isAliasedNodeData(value: Record<string, unknown>): boolean {
    if (typeof value !== "object" || value === null) {
        return false;
    }

    const keys = Object.keys(value);

    if (keys.length !== 3) {
        return false;
    }

    return ["node_value", "display_value", "details"].every((key) =>
        keys.includes(key),
    );
}

function recursivleyBuildDirtyStateTree(
    value: unknown,
): Record<string, unknown> | boolean | unknown[] | undefined {
    if (isAliasedNodeData(value as Record<string, unknown>)) {
        return false;
    }

    if (Array.isArray(value)) {
        const result = [];

        for (const arrayItem of value) {
            const transformed = recursivleyBuildDirtyStateTree(arrayItem);

            if (transformed !== undefined) {
                result.push(transformed);
            }
        }

        return result.length ? result : undefined;
    }

    if (value !== null && typeof value === "object") {
        const result: Record<string, unknown> = {};

        for (const [propertyName, propertyValue] of Object.entries(value)) {
            const transformed = recursivleyBuildDirtyStateTree(propertyValue);

            if (transformed !== undefined) {
                result[propertyName] = transformed;
            }
        }

        return Object.keys(result).length ? result : undefined;
    }

    return undefined;
}

export function generateWidgetDirtyStates(
    aliasedResourceData: ResourceData,
): WidgetDirtyStates {
    return recursivleyBuildDirtyStateTree(
        aliasedResourceData,
    ) as WidgetDirtyStates;
}
