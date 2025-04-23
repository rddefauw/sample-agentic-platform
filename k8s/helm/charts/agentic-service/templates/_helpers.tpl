{{- define "app.name" -}}
{{- .Release.Name }}
{{- end }}

{{- define "app.namespace" -}}
{{- .Release.Namespace }}
{{- end }}