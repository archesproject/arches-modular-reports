import type { ResourceData } from "@/arches_modular_reports/ModularReport/types.ts";
import type { WidgetDirtyStates } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/types.ts";
import type { AliasedTileData } from "@/arches_component_lab/types.ts";

function hasDirtyDescendant(
    branch: WidgetDirtyStates | WidgetDirtyStates[],
): boolean {
    if (Array.isArray(branch)) {
        return branch.some(function (item) {
            return hasDirtyDescendant(item);
        });
    }

    if (branch !== null && typeof branch === "object") {
        const objectToIterate = branch.aliased_data ?? branch;

        return Object.values(objectToIterate).some(function (child) {
            return hasDirtyDescendant(child);
        });
    }

    return branch === true;
}

function prune(
    resourceData: AliasedTileData | AliasedTileData[],
    widgetDirtyStates: WidgetDirtyStates | WidgetDirtyStates[],
): AliasedTileData | AliasedTileData[] | undefined {
    if (Array.isArray(resourceData)) {
        const prunedArray = resourceData.reduce(function (
            accumulatedItems,
            currentItem,
            indexInArray,
        ) {
            const dirtyItem =
                (widgetDirtyStates as WidgetDirtyStates[])[indexInArray] ||
                ({} as WidgetDirtyStates);

            if (
                currentItem !== null &&
                typeof currentItem === "object" &&
                "tileid" in currentItem
            ) {
                const prunedItem = prune(currentItem, dirtyItem) as
                    | AliasedTileData
                    | undefined;

                if (prunedItem) {
                    accumulatedItems.push(prunedItem);
                }
            } else if (currentItem !== null) {
                accumulatedItems.push(currentItem);
            }

            return accumulatedItems;
        }, [] as AliasedTileData[]);

        if (prunedArray.length === 0) {
            return undefined;
        }
        return prunedArray;
    }

    if (
        resourceData !== null &&
        typeof resourceData === "object" &&
        "tileid" in resourceData
    ) {
        if (!resourceData.tileid && !hasDirtyDescendant(widgetDirtyStates)) {
            return undefined;
        }

        const prunedAliasedData: AliasedTileData["aliased_data"] = {};

        Object.entries(resourceData.aliased_data!).forEach(function ([
            nodeAlias,
            aliasedDatum,
        ]) {
            const dirtyStates =
                (widgetDirtyStates as WidgetDirtyStates).aliased_data ?? {};
            const prunedChild = prune(
                aliasedDatum as AliasedTileData,
                (dirtyStates as WidgetDirtyStates)[
                    nodeAlias
                ] as WidgetDirtyStates,
            );

            if (prunedChild !== undefined) {
                prunedAliasedData[nodeAlias] = prunedChild;
            }
        });

        return {
            ...resourceData,
            aliased_data: prunedAliasedData,
        } as AliasedTileData;
    }

    return resourceData as AliasedTileData;
}

export function pruneResourceData(
    resourceData: ResourceData,
    widgetDirtyStates: WidgetDirtyStates,
): ResourceData {
    const prunedAliasedData = Object.entries(resourceData.aliased_data).reduce<
        ResourceData["aliased_data"]
    >(function (acc, [nodeAlias, aliasedDatum]) {
        const dirtyStates = (
            widgetDirtyStates.aliased_data as WidgetDirtyStates
        )[nodeAlias];
        const prunedData = prune(
            aliasedDatum as AliasedTileData,
            dirtyStates as WidgetDirtyStates,
        );

        if (prunedData !== undefined) {
            acc[nodeAlias] = prunedData;
        }

        return acc;
    }, {});

    return { ...resourceData, aliased_data: prunedAliasedData };
}
