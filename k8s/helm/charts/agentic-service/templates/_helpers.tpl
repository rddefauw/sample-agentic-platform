{{- define "app.name" -}}
{{- .Release.Name }}
{{- end }}

{{- define "app.namespace" -}}
{{- .Release.Namespace }}
{{- end }}

{{- define "app.image" -}}
{{- printf "%s.dkr.ecr.%s.amazonaws.com/%s:%s" .Values.aws.account .Values.aws.region .Values.image.repository .Values.image.tag -}}
{{- end }}

{{- define "app.irsaRoleArn" -}}
{{- if .Values.serviceAccount.irsaRoleName -}}
{{- printf "arn:aws:iam::%s:role/%s-%s" .Values.aws.account .Values.aws.stackPrefix .Values.serviceAccount.irsaRoleName -}}
{{- end -}}
{{- end }}