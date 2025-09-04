export function getValueFromPath(
    sourceObject: Record<string, unknown>,
    pathSegments: Array<string | number> | null | undefined,
): Record<string, unknown> | undefined {
    if (!pathSegments || pathSegments.length === 0) {
        return sourceObject;
    }

    let currentValue = sourceObject;

    for (const pathSegment of pathSegments) {
        currentValue = currentValue[pathSegment] as Record<string, unknown>;
    }

    return currentValue;
}
