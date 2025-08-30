import uniqueId from "es-toolkit/compat/uniqueId";

const objectIdentityCache = new WeakMap<object, string>();
const primitiveIdentityCache = new Map<unknown, string>();
const compositeTrieRoot = new Map<unknown, unknown>();
const compositeLeafMarker = Symbol("leaf");

export function generateStableKey(identityValue: unknown): string {
    if (identityValue !== null && typeof identityValue === "object") {
        if (Array.isArray(identityValue)) {
            let currentMapNode = compositeTrieRoot as Map<unknown, unknown>;
            for (const elementValue of identityValue) {
                let nextMapNode = currentMapNode.get(elementValue) as
                    | Map<unknown, unknown>
                    | undefined;
                if (!nextMapNode) {
                    nextMapNode = new Map<unknown, unknown>();
                    currentMapNode.set(elementValue, nextMapNode);
                }
                currentMapNode = nextMapNode;
            }
            const existingCompositeKey = currentMapNode.get(
                compositeLeafMarker,
            ) as string | undefined;
            if (existingCompositeKey) return existingCompositeKey;
            const generatedCompositeKey = uniqueId();
            currentMapNode.set(compositeLeafMarker, generatedCompositeKey);
            return generatedCompositeKey;
        }
        const existingObjectKey = objectIdentityCache.get(
            identityValue as object,
        );
        if (existingObjectKey) return existingObjectKey;
        const generatedObjectKey = uniqueId();
        objectIdentityCache.set(identityValue as object, generatedObjectKey);
        return generatedObjectKey;
    }
    const existingPrimitiveKey = primitiveIdentityCache.get(identityValue);
    if (existingPrimitiveKey) return existingPrimitiveKey;
    const generatedPrimitiveKey = uniqueId();
    primitiveIdentityCache.set(identityValue, generatedPrimitiveKey);
    return generatedPrimitiveKey;
}
