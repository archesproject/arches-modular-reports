export function compileGlobalCss(
    cssOverrides: Record<string, Record<string, string>>,
) {
    let ret = "";
    for (const [css_class_name, css_class_def] of Object.entries(
        cssOverrides,
    )) {
        ret += `${css_class_name}{`;
        for (const [style_prop, style_value] of Object.entries(
            css_class_def as Record<string, unknown>,
        )) {
            ret += `${style_prop}: ${style_value};`;
        }
        ret += `}`;
    }
    return ret;
}
