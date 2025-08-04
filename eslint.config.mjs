
import js from "@eslint/js";
import * as importX from "eslint-plugin-import-x";
import pluginVue from 'eslint-plugin-vue';
import tseslint from 'typescript-eslint';
import eslintConfigPrettier from "eslint-config-prettier";

import vueESLintParser from 'vue-eslint-parser';

export default [
    js.configs.recommended,
    importX.flatConfigs.recommended,
    importX.flatConfigs.typescript,
    ...pluginVue.configs['flat/recommended'],
    ...tseslint.configs.recommended,
    eslintConfigPrettier,
    {
        "languageOptions": {
            "globals": {
                "define": false,
                "require": false,
                "window": false,
                "console": false,
                "history": false,
                "location": false,
                "Promise": false,
                "setTimeout": false,
                "URL": false,
                "URLSearchParams": false,
                "fetch": false
            },
            "parser": vueESLintParser,
            "parserOptions": {
                "ecmaVersion": 11,
                "sourceType": "module",
                "requireConfigFile": false,
                "parser": {
                    "ts": "@typescript-eslint/parser"
                }
            },
        },
        "rules": {
            "@typescript-eslint/no-unused-vars": [
                "error", { "argsIgnorePattern": "^_", "varsIgnorePattern": "^_" }
            ],
            "semi": ["error", "always"],
            "import-x/no-unresolved": [
                "error",
                { ignore: ["arches"] }
            ],
            "import-x/order": "error",
        },
    },
];
