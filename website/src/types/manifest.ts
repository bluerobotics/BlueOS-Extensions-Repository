export interface Author {
    name: string;
    email: string;
}

export interface Company {
    name: string;
    about?: string;
    email?: string;
}

export enum ExtensionType {
    DEVICE_INTEGRATION = "device-integration",
    THEME = "theme",
    OTHER = "other",
    TOOL = "tool",
    EXAMPLE = "example"
}

export interface Version {
    permissions?: {[key: string]: any};
    requirements?: string;
    tag?: string;
    website: string;
    authors: Author[];
    docs?: string;
    readme?: string;
    company?: Company;
    support?: string;
    type: ExtensionType;
    filter_tags: string[];
    extra_links: {[key: string]: string};
}

export interface RepositoryEntry {
    identifier: string;
    name: string;
    description: string;
    docker: string;
    website: string;
    versions: {[key: string]: Version};
    extension_logo?: string;
    company_logo?: string;
}
