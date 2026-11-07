
CREATE FUNCTION cestas_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Historico imutavel: use anotacao de correcao auditada' USING ERRCODE='23514'; END $$;
CREATE FUNCTION cestas_family_update() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.id IS DISTINCT FROM OLD.id OR NEW.identity IS DISTINCT FROM OLD.identity THEN
  RAISE EXCEPTION 'Identificador permanente' USING ERRCODE='23514';
 END IF;
 IF NEW.responsible_id IS DISTINCT FROM OLD.responsible_id AND (
 NOT EXISTS(SELECT 1 FROM core_membership WHERE family_id=NEW.id AND person_id=NEW.responsible_id AND ended_at IS NULL)
 OR NOT EXISTS(SELECT 1 FROM core_document WHERE person_id=NEW.responsible_id)
 OR EXISTS(SELECT 1 FROM core_family WHERE responsible_id=NEW.responsible_id AND id<>NEW.id)) THEN
  RAISE EXCEPTION 'Responsavel precisa ser integrante identificado de uma familia' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION cestas_insert() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_TABLE_NAME='core_family' THEN
  IF EXISTS(SELECT 1 FROM core_family WHERE responsible_id=NEW.responsible_id)
  OR EXISTS(SELECT 1 FROM core_membership WHERE person_id=NEW.responsible_id AND relationship='Responsável original') THEN
   RAISE EXCEPTION 'Responsavel ja vinculado: reutilize familia permanente' USING ERRCODE='23514';
  END IF;
 ELSIF TG_TABLE_NAME='core_document' THEN
  IF NEW.number !~ '^[A-Z0-9]+$' THEN RAISE EXCEPTION 'Documento nao normalizado' USING ERRCODE='23514'; END IF;
 ELSIF TG_TABLE_NAME='core_benefit' THEN
  IF NEW.policy->>'months' IS DISTINCT FROM '6'
  OR NEW.policy->>'renewable' IS DISTINCT FROM 'false'
  OR NEW.policy->>'missed_accumulate' IS DISTINCT FROM 'false'
  OR jsonb_array_length(NEW.policy->'periods') IS DISTINCT FROM 6
  OR NEW.mode NOT IN ('calendar','anniversary')
  OR NEW.policy->>'mode' IS DISTINCT FROM NEW.mode
  OR NEW.policy->'periods'->0->>'start' IS DISTINCT FROM NEW.original_start::text THEN
   RAISE EXCEPTION 'Beneficio deve preservar seis periodos sem renovacao' USING ERRCODE='23514';
  END IF;
 ELSIF TG_TABLE_NAME='core_period' THEN
  IF NEW.start::text IS DISTINCT FROM (SELECT policy->'periods'->(NEW.number-1)->>'start' FROM core_benefit WHERE id=NEW.benefit_id)
  OR NEW."end"::text IS DISTINCT FROM (SELECT policy->'periods'->(NEW.number-1)->>'end' FROM core_benefit WHERE id=NEW.benefit_id) THEN
   RAISE EXCEPTION 'Periodo difere da regra original' USING ERRCODE='23514';
  END IF;
 ELSIF TG_TABLE_NAME='core_delivery' THEN
  IF NOT EXISTS(SELECT 1 FROM core_period p JOIN core_benefit b ON b.id=p.benefit_id
  JOIN core_membership m ON m.family_id=b.family_id AND m.person_id=NEW.recipient_id AND m.ended_at IS NULL
  WHERE p.id=NEW.period_id AND NEW.delivered_on>=p.start AND NEW.delivered_on<p."end") THEN
   RAISE EXCEPTION 'Entrega fora do periodo ou pessoa sem vinculo' USING ERRCODE='23514';
  END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER protect_core_benefit BEFORE UPDATE OR DELETE ON core_benefit FOR EACH ROW EXECUTE FUNCTION cestas_immutable();
CREATE TRIGGER protect_core_period BEFORE UPDATE OR DELETE ON core_period FOR EACH ROW EXECUTE FUNCTION cestas_immutable();
CREATE TRIGGER protect_core_delivery BEFORE UPDATE OR DELETE ON core_delivery FOR EACH ROW EXECUTE FUNCTION cestas_immutable();
CREATE TRIGGER protect_core_audit BEFORE UPDATE OR DELETE ON core_audit FOR EACH ROW EXECUTE FUNCTION cestas_immutable();
CREATE TRIGGER protect_core_document BEFORE UPDATE OR DELETE ON core_document FOR EACH ROW EXECUTE FUNCTION cestas_immutable();
CREATE TRIGGER protect_core_membership BEFORE UPDATE OR DELETE ON core_membership FOR EACH ROW EXECUTE FUNCTION cestas_immutable();
CREATE TRIGGER protect_core_family_delete BEFORE DELETE ON core_family FOR EACH ROW EXECUTE FUNCTION cestas_immutable();
CREATE TRIGGER protect_core_person_delete BEFORE DELETE ON core_person FOR EACH ROW EXECUTE FUNCTION cestas_immutable();
CREATE TRIGGER protect_family_identity BEFORE UPDATE ON core_family FOR EACH ROW EXECUTE FUNCTION cestas_family_update();
CREATE TRIGGER check_insert_core_family BEFORE INSERT ON core_family FOR EACH ROW EXECUTE FUNCTION cestas_insert();
CREATE TRIGGER check_insert_core_document BEFORE INSERT ON core_document FOR EACH ROW EXECUTE FUNCTION cestas_insert();
CREATE TRIGGER check_insert_core_benefit BEFORE INSERT ON core_benefit FOR EACH ROW EXECUTE FUNCTION cestas_insert();
CREATE TRIGGER check_insert_core_period BEFORE INSERT ON core_period FOR EACH ROW EXECUTE FUNCTION cestas_insert();
CREATE TRIGGER check_insert_core_delivery BEFORE INSERT ON core_delivery FOR EACH ROW EXECUTE FUNCTION cestas_insert();
