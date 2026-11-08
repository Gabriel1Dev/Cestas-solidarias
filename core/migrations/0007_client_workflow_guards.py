from django.db import migrations

SQL = r"""
CREATE OR REPLACE FUNCTION cestas_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE policy_benefit core_benefit%ROWTYPE; x core_extensionauthorization%ROWTYPE; prior_end date; expected_start date; expected_end date; month_start date; extension_index integer;
BEGIN
 IF TG_TABLE_NAME='core_family' THEN
  IF EXISTS(SELECT 1 FROM core_family WHERE responsible_id=NEW.responsible_id)
  OR EXISTS(SELECT 1 FROM core_membership WHERE person_id=NEW.responsible_id AND relationship='Responsável original') THEN
   RAISE EXCEPTION 'Responsavel ja vinculado: reutilize familia permanente' USING ERRCODE='23514';
  END IF;
 ELSIF TG_TABLE_NAME='core_document' THEN
  IF NEW.number !~ '^[A-Z0-9]+$' THEN RAISE EXCEPTION 'Documento nao normalizado' USING ERRCODE='23514'; END IF;
 ELSIF TG_TABLE_NAME='core_benefit' THEN
  IF NEW.policy->>'version'='3' THEN
   IF COALESCE(NEW.policy->>'months','') NOT IN ('1','2','3')
    OR NEW.policy->>'mode' IS DISTINCT FROM 'distribution'
    OR NEW.mode IS DISTINCT FROM 'distribution'
    OR COALESCE(NEW.policy->>'has_children','') NOT IN ('true','false')
    OR (NEW.policy->>'has_children'='false' AND NEW.policy->>'months'<>'1')
    OR jsonb_array_length(NEW.policy->'periods') IS DISTINCT FROM (NEW.policy->>'months')::integer
    OR NEW.policy->>'renewable' IS DISTINCT FROM 'false'
    OR NEW.policy->>'missed_accumulate' IS DISTINCT FROM 'false'
    OR (NEW.original_start > (NEW.policy->'periods'->0->>'start')::date) THEN
     RAISE EXCEPTION 'Politica de triagem/duracao invalida' USING ERRCODE='23514';
   END IF;
  ELSE
   IF (COALESCE(NEW.policy->>'months','') NOT IN ('1','2','3','6') OR (NEW.policy->>'months'='6' AND NEW.policy->>'version' IS DISTINCT FROM '1') OR (NEW.policy->>'months' IN ('1','2','3') AND (NEW.policy->>'version' IS DISTINCT FROM '2' OR COALESCE(NEW.policy->>'has_children','') NOT IN ('true','false') OR (NEW.policy->>'has_children'='false' AND NEW.policy->>'months'<>'1'))))
    OR NEW.policy->>'renewable' IS DISTINCT FROM 'false'
    OR NEW.policy->>'missed_accumulate' IS DISTINCT FROM 'false'
    OR jsonb_array_length(NEW.policy->'periods') IS DISTINCT FROM (NEW.policy->>'months')::integer
    OR NEW.mode NOT IN ('calendar','anniversary')
    OR NEW.policy->>'mode' IS DISTINCT FROM NEW.mode
    OR NEW.policy->'periods'->0->>'start' IS DISTINCT FROM NEW.original_start::text THEN
     RAISE EXCEPTION 'Politica de duracao invalida' USING ERRCODE='23514';
   END IF;
  END IF;
 ELSIF TG_TABLE_NAME='core_period' THEN
  SELECT * INTO policy_benefit FROM core_benefit WHERE id=NEW.benefit_id;
  IF NEW.extension_id IS NULL THEN
   IF NEW.start::text IS DISTINCT FROM (policy_benefit.policy->'periods'->(NEW.number-1)->>'start')
    OR NEW."end"::text IS DISTINCT FROM (policy_benefit.policy->'periods'->(NEW.number-1)->>'end') THEN
     RAISE EXCEPTION 'Periodo difere da regra original' USING ERRCODE='23514';
   END IF;
   IF policy_benefit.policy->>'version'='3' AND (NEW.scheduled_on IS DISTINCT FROM NEW.start OR EXTRACT(DOW FROM NEW.start)<>6 OR EXTRACT(DAY FROM NEW.start)<8 OR EXTRACT(DAY FROM NEW.start)>14) THEN
    RAISE EXCEPTION 'Agendamento precisa ser no segundo sabado' USING ERRCODE='23514';
   END IF;
  ELSE
   SELECT * INTO x FROM core_extensionauthorization WHERE id=NEW.extension_id;
   SELECT "end" INTO prior_end FROM core_period WHERE benefit_id=NEW.benefit_id AND number=NEW.number-1;
   extension_index := (SELECT COUNT(*)+1 FROM core_period WHERE extension_id=x.id);
   month_start := date_trunc('month', (x.authorized_at AT TIME ZONE 'America/Sao_Paulo')::date)::date;
   expected_start := month_start + ((6 - EXTRACT(DOW FROM month_start)::int + 7) % 7) + 7;
   IF expected_start < (x.authorized_at AT TIME ZONE 'America/Sao_Paulo')::date THEN
    month_start := (month_start + interval '1 month')::date;
    expected_start := month_start + ((6 - EXTRACT(DOW FROM month_start)::int + 7) % 7) + 7;
   END IF;
   expected_start := (date_trunc('month', expected_start + ((extension_index-1)||' month')::interval))::date + ((6 - EXTRACT(DOW FROM date_trunc('month', expected_start + ((extension_index-1)||' month')::interval))::int + 7) % 7) + 7;
   expected_end := (date_trunc('month', expected_start + interval '1 month')::date + ((6 - EXTRACT(DOW FROM date_trunc('month', expected_start + interval '1 month')::date)::int + 7) % 7) + 7);
   IF x.benefit_id IS DISTINCT FROM NEW.benefit_id OR x.months < extension_index OR NEW.number IS DISTINCT FROM (SELECT COALESCE(MAX(number),0)+1 FROM core_period WHERE benefit_id=NEW.benefit_id)
    OR (extension_index=1 AND NEW.start IS DISTINCT FROM expected_start) OR (extension_index>1 AND prior_end IS DISTINCT FROM NEW.start) OR NEW.start IS DISTINCT FROM expected_start
    OR NEW."end" IS DISTINCT FROM expected_end OR NEW.scheduled_on IS DISTINCT FROM NEW.start
    OR EXTRACT(DOW FROM NEW.start)<>6 OR EXTRACT(DAY FROM NEW.start)<8 OR EXTRACT(DAY FROM NEW.start)>14 THEN
     RAISE EXCEPTION 'Periodo de prorrogacao invalido' USING ERRCODE='23514';
   END IF;
  END IF;
 ELSIF TG_TABLE_NAME='core_delivery' THEN
  IF NOT EXISTS(SELECT 1 FROM core_period p JOIN core_benefit b ON b.id=p.benefit_id JOIN core_family f ON f.id=b.family_id
    JOIN core_membership m ON m.family_id=b.family_id AND m.person_id=NEW.recipient_id AND m.ended_at IS NULL
    WHERE p.id=NEW.period_id AND f.status='approved' AND NEW.delivered_on>=p.start AND NEW.delivered_on<p."end"
      AND (NEW.historical OR b.policy->>'version'<>'3' OR p.scheduled_on=NEW.delivered_on OR EXISTS(SELECT 1 FROM core_scheduleauthorization a WHERE a.period_id=p.id AND a.date=NEW.delivered_on))) THEN
   RAISE EXCEPTION 'Entrega fora do periodo/agendamento ou pessoa sem vinculo' USING ERRCODE='23514';
  END IF;
 ELSIF TG_TABLE_NAME='core_extensionauthorization' THEN
  IF NEW.months<1 OR NEW.months>6 OR length(trim(NEW.reason))<10 OR NOT EXISTS(SELECT 1 FROM auth_user WHERE id=NEW.authorized_by_id AND is_superuser) THEN
   RAISE EXCEPTION 'Prorrogacao requer autorizacao da coordenacao' USING ERRCODE='23514';
  END IF;
 ELSIF TG_TABLE_NAME='core_scheduleauthorization' THEN
  IF NEW.date<(now() AT TIME ZONE 'America/Sao_Paulo')::date OR length(trim(NEW.reason))<10 OR NOT EXISTS(SELECT 1 FROM auth_user WHERE id=NEW.authorized_by_id AND is_superuser)
   OR EXISTS(SELECT 1 FROM core_delivery WHERE period_id=NEW.period_id) THEN
   RAISE EXCEPTION 'Reagendamento requer autorizacao da coordenacao' USING ERRCODE='23514';
  END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE OR REPLACE FUNCTION cestas_family_update() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.id IS DISTINCT FROM OLD.id OR NEW.identity IS DISTINCT FROM OLD.identity THEN RAISE EXCEPTION 'Identificador permanente' USING ERRCODE='23514'; END IF;
 IF NEW.responsible_id IS DISTINCT FROM OLD.responsible_id AND (
  NOT EXISTS(SELECT 1 FROM core_membership WHERE family_id=NEW.id AND person_id=NEW.responsible_id AND ended_at IS NULL)
  OR NOT EXISTS(SELECT 1 FROM core_document WHERE person_id=NEW.responsible_id AND kind='CPF')
  OR EXISTS(SELECT 1 FROM core_family WHERE responsible_id=NEW.responsible_id AND id<>NEW.id)) THEN
  RAISE EXCEPTION 'Responsavel precisa ser integrante identificado de uma familia' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER check_insert_core_extensionauthorization BEFORE INSERT ON core_extensionauthorization FOR EACH ROW EXECUTE FUNCTION cestas_insert();
CREATE TRIGGER check_insert_core_scheduleauthorization BEFORE INSERT ON core_scheduleauthorization FOR EACH ROW EXECUTE FUNCTION cestas_insert();
CREATE TRIGGER protect_core_extensionauthorization BEFORE UPDATE OR DELETE ON core_extensionauthorization FOR EACH ROW EXECUTE FUNCTION cestas_immutable();
CREATE TRIGGER protect_core_scheduleauthorization BEFORE UPDATE OR DELETE ON core_scheduleauthorization FOR EACH ROW EXECUTE FUNCTION cestas_immutable();
"""

class Migration(migrations.Migration):
    dependencies=[('core','0006_extension_period_limit')]
    operations=[migrations.RunSQL(SQL, migrations.RunSQL.noop)]
