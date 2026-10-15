import { describe, expect, it } from "vitest";

import { resolveWorkspaces } from "@/arches_modular_reports/ResourceReport/utils/resolve-workspaces.ts";

import type { WorkspaceConfig } from "@/arches_modular_reports/ResourceReport/types.ts";

const WORKSPACE_CONFIGS: WorkspaceConfig[] = [
    {
        id: "report",
        component: "ReportWorkspace",
        label: { en: "Report" },
        description: { en: "A curated summary" },
    },
    { id: "data", component: "DataWorkspace", label: "Data" },
    { id: "custom", component: "my_app/Report/CustomWorkspace" },
];

describe("resolveWorkspaces", () => {
    it("hides the data workspace from users who cannot edit", () => {
        const workspaces = resolveWorkspaces(WORKSPACE_CONFIGS, {
            canEdit: false,
            activeLanguage: "en",
        });

        expect(workspaces.map((workspace) => workspace.id)).toEqual([
            "report",
            "custom",
        ]);
    });
});
