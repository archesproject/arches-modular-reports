from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("arches_modular_reports", "0002_add_modular_report"),
    ]

    forward_sql_string = """
        CREATE OR REPLACE FUNCTION __arches_get_concept_valueid(
            concept_value UUID,
            language_id   TEXT DEFAULT 'en'
        )
        RETURNS TEXT
        LANGUAGE 'plpgsql'
        COST 100
        VOLATILE PARALLEL UNSAFE
        AS $BODY$

        DECLARE
            concept_id        TEXT := '';
            normalized_lang_id TEXT;
            base_lang_id       TEXT;
        BEGIN
            IF concept_value IS NULL THEN
                RETURN concept_id;
            END IF;

            normalized_lang_id := replace(language_id, '_', '-');
            base_lang_id       := split_part(normalized_lang_id, '-', 1);

            SELECT c.conceptid::text
            INTO concept_id
            FROM values v_orig
            JOIN concepts c   ON v_orig.conceptid = c.conceptid
            JOIN values v_lang 
                ON c.conceptid = v_lang.conceptid
            WHERE v_orig.valueid = concept_value
            AND v_lang.valuetype = 'prefLabel'
            AND (
                v_lang.languageid = normalized_lang_id
                OR v_lang.languageid = base_lang_id
                OR v_lang.languageid LIKE base_lang_id || '-%'
                OR v_lang.languageid LIKE base_lang_id || '_%'
            )
            ORDER BY
            CASE
                WHEN v_lang.languageid = normalized_lang_id THEN 1

                WHEN (
                        normalized_lang_id = base_lang_id 
                        AND 
                        (
                        v_lang.languageid LIKE base_lang_id || '-%' 
                        OR v_lang.languageid LIKE base_lang_id || '_%'
                        )
                    )
                    OR (
                        normalized_lang_id != base_lang_id 
                        AND v_lang.languageid = base_lang_id
                    ) THEN 2

                WHEN v_lang.languageid LIKE base_lang_id || '-%' 
                    OR v_lang.languageid LIKE base_lang_id || '_%' THEN 3

                ELSE 4
            END
            LIMIT 1;

            IF concept_id IS NULL THEN
                concept_id := '';
            END IF;

            RETURN concept_id;
        END;

        $BODY$;


        CREATE OR REPLACE FUNCTION public.__arches_get_concept_list_valueids(
            concept_array jsonb,
            language_id text DEFAULT 'en'
        )
        RETURNS jsonb
        LANGUAGE 'plpgsql'
        COST 100
        VOLATILE PARALLEL UNSAFE

        AS $BODY$
        BEGIN
            IF concept_array IS NULL OR concept_array::text = 'null' THEN
                RETURN '[]'::jsonb;
            END IF;

            RETURN COALESCE(
                (
                    SELECT jsonb_agg(d.valueid)
                    FROM (
                        SELECT __arches_get_concept_valueid(x.conceptid::uuid, language_id) AS valueid
                        FROM (
                            SELECT json_array_elements_text(concept_array::json) AS conceptid
                        ) x
                    ) d
                ),
                '[]'::jsonb 
            );
        END;

        $BODY$;


        CREATE OR REPLACE FUNCTION public.__arches_get_valueid(
            in_tiledata jsonb,
            in_nodeid uuid,
            language_id text DEFAULT 'en'
        )

        RETURNS text
        LANGUAGE 'plpgsql'
        COST 100
        VOLATILE PARALLEL UNSAFE

        AS $BODY$
            declare
                value   text := '';
                in_node_type    text;
                in_node_config  json;
            begin
                if in_nodeid is null or in_nodeid is null then
                    return '<invalid_nodeid>';
                end if;

                if in_tiledata is null then
                    return '';
                end if;

                select n.datatype, n.config
                into in_node_type, in_node_config
                from nodes n where nodeid = in_nodeid::uuid;

                if in_node_type in ('semantic', 'geojson-feature-collection', 'annotation') then
                    return 'unsupported node type (' || in_node_type || ')';
                end if;

                if in_node_type is null then
                    return '';
                end if;

                case in_node_type
                    when 'concept' then
                        value := __arches_get_concept_valueid((in_tiledata ->> in_nodeid::text)::uuid);
                    when 'concept-list' then
                        value := __arches_get_concept_list_valueids(in_tiledata -> in_nodeid::text);
                    when 'resource-instance' then
                        value := __arches_get_resourceinstance_id(in_tiledata -> in_nodeid::text, 'name', language_id);
                    when 'resource-instance-list' then
                        value := __arches_get_resourceinstance_id_list(in_tiledata -> in_nodeid::text, 'name', language_id);
                    when 'url' then
                        value := in_tiledata -> in_nodeid::text ->> 'url';
                    else
                        value := null;
                end case;

                return value;
            end;

                
            $BODY$;


        CREATE OR REPLACE FUNCTION __arches_get_concept_label_v2(
            concept_value UUID,
            language_id TEXT DEFAULT 'en'
        )

        RETURNS TEXT
        LANGUAGE 'plpgsql'
        COST 100
        VOLATILE PARALLEL UNSAFE

        AS $BODY$

        DECLARE
            concept_label      TEXT := '';
            normalized_lang_id TEXT;
            base_lang_id       TEXT;
        BEGIN
            IF concept_value IS NULL THEN
                RETURN concept_label;
            END IF;

            normalized_lang_id := replace(language_id, '_', '-');
            base_lang_id := split_part(normalized_lang_id, '-', 1);

            SELECT v_lang.value
            INTO concept_label
            FROM values v_orig
            JOIN concepts c ON v_orig.conceptid = c.conceptid
            JOIN values v_lang ON c.conceptid = v_lang.conceptid
            WHERE v_orig.valueid = concept_value
            AND v_lang.valuetype = 'prefLabel'
            AND (
                v_lang.languageid = normalized_lang_id
                OR v_lang.languageid = base_lang_id
                OR v_lang.languageid LIKE base_lang_id || '-%'
                OR v_lang.languageid LIKE base_lang_id || '_%'
            )
            ORDER BY
                CASE
                    WHEN v_lang.languageid = normalized_lang_id THEN 1

                    WHEN (normalized_lang_id = base_lang_id AND 
                        (v_lang.languageid LIKE base_lang_id || '-%' OR v_lang.languageid LIKE base_lang_id || '_%'))
                        OR
                        (normalized_lang_id != base_lang_id AND v_lang.languageid = base_lang_id) THEN 2

                    WHEN v_lang.languageid LIKE base_lang_id || '-%' 
                        OR v_lang.languageid LIKE base_lang_id || '_%' THEN 3

                    ELSE 4
                END
            LIMIT 1;

            IF concept_label IS NULL THEN
                concept_label := '';
            END IF;

            RETURN concept_label;
        END;

        $BODY$;

        CREATE OR REPLACE FUNCTION public.__arches_get_concept_list_label_v2(
            concept_array jsonb,
            language_id text DEFAULT 'en'
        )
        RETURNS jsonb  
        LANGUAGE 'plpgsql'
        COST 100
        VOLATILE PARALLEL UNSAFE
        AS $BODY$
        DECLARE
            labels_jsonb jsonb := '[]'::jsonb;
        BEGIN
            IF concept_array IS NULL OR concept_array::text = 'null' THEN
                RETURN labels_jsonb;
            END IF;

            SELECT COALESCE(jsonb_agg(label), '[]'::jsonb)
            INTO labels_jsonb
            FROM (
                SELECT __arches_get_concept_label_v2(conceptid::uuid, language_id) AS label
                FROM json_array_elements_text(concept_array::json) AS elem(conceptid)
            ) sub;

            RETURN labels_jsonb;
        END;
        
        $BODY$;


        CREATE OR REPLACE FUNCTION public.__arches_get_resourceinstance_list_label_v2(
            resourceinstance_value jsonb,
            label_type text DEFAULT 'name'::text,
            language_id text DEFAULT 'en'
        )
        RETURNS jsonb
        LANGUAGE 'plpgsql'
        COST 100
        VOLATILE PARALLEL UNSAFE
        AS $BODY$
        DECLARE
            return_label jsonb := '[]'::jsonb;
        BEGIN
            IF resourceinstance_value IS NULL OR resourceinstance_value::text = 'null' THEN
                RETURN return_label;
            END IF;
            
            SELECT jsonb_agg(dvl.label)
            INTO return_label
            FROM (
                SELECT __arches_get_resourceinstance_label(dv.resource_instance, label_type, language_id) AS label
                FROM (
                    SELECT jsonb_array_elements(resourceinstance_value) AS resource_instance
                ) dv
            ) dvl;
            
            IF return_label IS NULL THEN
                return_label := '[]'::jsonb;
            END IF;
            
            RETURN return_label;
        END;

        $BODY$;

        CREATE OR REPLACE FUNCTION public.__arches_get_resourceinstance_id_list(
            resourceinstance_value jsonb,
            label_type text DEFAULT 'name'::text, 
            language_id text DEFAULT 'en'          
        )
        RETURNS jsonb
        LANGUAGE 'plpgsql'
        COST 100
        VOLATILE PARALLEL UNSAFE
        AS $BODY$
        DECLARE
            return_id_list jsonb := '[]'::jsonb; 
        BEGIN
            IF resourceinstance_value IS NULL OR resourceinstance_value::text = 'null' THEN
                RETURN return_id_list;
            END IF;
            
            SELECT jsonb_agg(dvl.resourceinstance_id)  
            INTO return_id_list
            FROM (
                SELECT public.__arches_get_resourceinstance_id(dv.resource_instance, label_type, language_id) AS resourceinstance_id
                FROM (
                    SELECT jsonb_array_elements(resourceinstance_value) AS resource_instance
                ) dv
            ) dvl;
            
            IF return_id_list IS NULL THEN
                return_id_list := '[]'::jsonb;
            END IF;
            
            RETURN return_id_list;
        END;
        $BODY$;

        CREATE OR REPLACE FUNCTION public.__arches_get_resourceinstance_id(
            resourceinstance_value jsonb,
            label_type text DEFAULT 'name'::text,  
            language_id text DEFAULT 'en'        
        )
        RETURNS text
        LANGUAGE 'plpgsql'
        COST 100
        VOLATILE PARALLEL UNSAFE
        AS $BODY$
        DECLARE
            return_id          text := '';
            target_resourceid  uuid;
        BEGIN

            IF resourceinstance_value IS NULL OR resourceinstance_value::text = 'null' THEN
                RETURN return_id;
            END IF;
            
            target_resourceid := ((resourceinstance_value -> 0) ->> 'resourceId')::uuid;
            
            IF target_resourceid IS NULL THEN
                target_resourceid := (resourceinstance_value ->> 'resourceId')::uuid;
            END IF;
            
            IF target_resourceid IS NULL THEN
                RETURN return_id;
            END IF;
            
            IF EXISTS (
                SELECT 1
                FROM resource_instances r
                WHERE r.resourceinstanceid = target_resourceid
            ) THEN
                return_id := target_resourceid::text;
            ELSE
                return_id := NULL;
            END IF;

            RETURN return_id;
        END;
        $BODY$;

            CREATE OR REPLACE FUNCTION public.__arches_get_node_display_value_v2(
                in_tiledata jsonb,
                in_nodeid uuid,
                language_id text DEFAULT 'en')
                RETURNS text
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE PARALLEL UNSAFE
            AS $BODY$
                    declare
                        display_value   text := '';
                        in_node_type    text;
                        in_node_config  json;
                    begin
                        if in_nodeid is null or in_nodeid is null then
                            return '<invalid_nodeid>';
                        end if;

                        if in_tiledata is null then
                            return '';
                        end if;

                        select n.datatype, n.config
                        into in_node_type, in_node_config
                        from nodes n where nodeid = in_nodeid::uuid;

                        if in_node_type in ('semantic', 'geojson-feature-collection', 'annotation') then
                            return 'unsupported node type (' || in_node_type || ')';
                        end if;

                        if in_node_type is null then
                            return '';
                        end if;

                        case in_node_type
                            when 'string' then
                                display_value := ((in_tiledata -> in_nodeid::text) -> language_id) ->> 'value';
                            when 'concept' then
                                display_value := __arches_get_concept_label_v2((in_tiledata ->> in_nodeid::text)::uuid);
                            when 'concept-list' then
                                display_value := __arches_get_concept_list_label_v2(in_tiledata -> in_nodeid::text);
                            when 'reference' then
								display_value := __arches_controlled_lists_get_reference_label_list(in_tiledata -> in_nodeid::text, language_id);
                            when 'edtf' then
                                display_value := (in_tiledata ->> in_nodeid::text);
                            when 'file-list' then
                                display_value := __arches_get_file_list_label(in_tiledata -> in_nodeid::text, language_id);
                            when 'domain-value' then
                                display_value := __arches_get_domain_label((in_tiledata ->> in_nodeid::text)::uuid, in_nodeid, language_id);
                            when 'domain-value-list' then
                                display_value := __arches_get_domain_list_label(in_tiledata -> in_nodeid::text, in_nodeid, language_id);
                            when 'url' then
								if length(in_tiledata -> in_nodeid::text ->> 'url_label') > 0 then
									display_value := (in_tiledata -> in_nodeid::text)::jsonb ->> 'url_label';
								else
								 	display_value := (in_tiledata -> in_nodeid::text)::jsonb ->> 'url';
								end if;
                            when 'node-value' then
                                display_value := __arches_get_nodevalue_label(in_tiledata -> in_nodeid::text, in_nodeid);
                            when 'resource-instance' then
                                display_value := __arches_get_resourceinstance_label(in_tiledata -> in_nodeid::text, 'name', language_id);
                            when 'resource-instance-list' then
                                display_value := __arches_get_resourceinstance_list_label_v2(in_tiledata -> in_nodeid::text, 'name', language_id);
                            when 'date' then
                                display_value := TO_CHAR((in_tiledata ->> in_nodeid::text)::timestamp, in_node_config ->> 'dateFormat');
                            else
                                display_value := (in_tiledata ->> in_nodeid::text)::text;

                            end case;

                        return display_value;
                    end;

                        
            $BODY$;
        """

    reverse_sql_string = """
            drop function if exists __arches_get_node_display_value_v2;
            drop function if exists __arches_get_concept_list_label_v2;
            drop function if exists __arches_get_concept_label_v2;
            drop function if exists __arches_get_concept_valueid;
            drop function if exists __arches_get_concept_list_valueids;
            drop function if exists __arches_get_resourceinstance_list_label_v2;
            drop function if exists __arches_get_resourceinstance_id_list;
            drop function if exists __arches_get_resourceinstance_id;
            drop function if exists __arches_get_valueid;
        """

    operations = [
        migrations.RunSQL(forward_sql_string, reverse_sql_string),
    ]
