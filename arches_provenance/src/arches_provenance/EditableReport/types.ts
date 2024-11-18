export interface Settings {
    ACTIVE_LANGUAGE: string;
    ACTIVE_LANGUAGE_DIRECTION: string;
}

export interface NamedSection {
    name: string;
    content: SectionContent[];
}

export interface SectionContent {
    component: string;
    config: { [key: string]: any };
}
