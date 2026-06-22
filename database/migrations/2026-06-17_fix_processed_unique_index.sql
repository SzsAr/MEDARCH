-- Ajusta la regla de duplicados para que solo aplique a documentos procesados.
-- Necesario si la base ya tenia ux_doc_unico creado sin WHERE estado = 'PROCESADO'.

DROP INDEX IF EXISTS gesdoc.ux_doc_unico;

CREATE UNIQUE INDEX ux_doc_unico
ON gesdoc.documentos (id_paciente, id_tipo, fecha, consecutivo)
WHERE estado = 'PROCESADO';
