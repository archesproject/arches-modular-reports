import uniqueId from "es-toolkit/compat/uniqueId";

const objectKeyCache = new WeakMap<object, string>();
const primitiveKeyCache = new Map<unknown, string>();

const compositeLeafMarker = Symbol("composite-leaf");
const compositeRootNode = new Map();

function getCompositeArrayKey(elementValues: unknown[]): string {
    let currentNode = compositeRootNode;

    for (const elementValue of elementValues) {
        const elementStableKey = generateStableKey(elementValue);
        const existingChild = currentNode.get(elementStableKey);

        let nextNode;
        if (existingChild instanceof Map) {
            nextNode = existingChild;
        } else {
            nextNode = new Map();
            currentNode.set(elementStableKey, nextNode);
        }

        currentNode = nextNode;
    }

    const existingCompositeKey = currentNode.get(compositeLeafMarker);
    if (typeof existingCompositeKey === "string") {
        return existingCompositeKey;
    }

    const generatedKey = uniqueId();
    currentNode.set(compositeLeafMarker, generatedKey);

    return generatedKey;
}

export function generateStableKey(identityValue: unknown): string {
    if (Array.isArray(identityValue)) {
        return getCompositeArrayKey(identityValue);
    }

    if (identityValue && typeof identityValue === "object") {
        const cachedObjectKey = objectKeyCache.get(identityValue);
        if (cachedObjectKey) {
            return cachedObjectKey;
        }

        const generatedObjectKey = uniqueId();
        objectKeyCache.set(identityValue, generatedObjectKey);
        return generatedObjectKey;
    }

    const cachedPrimitiveKey = primitiveKeyCache.get(identityValue);
    if (cachedPrimitiveKey) {
        return cachedPrimitiveKey;
    }

    const generatedPrimitiveKey = uniqueId();
    primitiveKeyCache.set(identityValue, generatedPrimitiveKey);
    return generatedPrimitiveKey;
}
