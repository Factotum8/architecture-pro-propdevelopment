# Отчёт по результатам анализа Kubernetes Audit Log

## Подозрительные события

1. Доступ к секретам:
   - Кто: system:serviceaccount:secure-ops:monitoring
   - Где: namespace kube-system
   - Почему подозрительно: Пытается получить (прочитать) один из default-token секретов в namespace kube-system, притворяясь сервис-аккаунтом monitoring

2. Привилегированные поды:
   - Кто: system:serviceaccount:secure-ops:monitoring 
   - Комментарий: Создаёт Pod privileged-pod с securityContext.privileged: true — контейнер запустится в привилегированном режиме (near-host privileges)

3. Использование kubectl exec в чужом поде:
   - Кто: system:serviceaccount:secure-ops:monitoring
   - Что делал: Выполняет в поде coredns команду cat /etc/resolv.conf,

4. Создание RoleBinding с правами cluster-admin:
   - Кто: system:serviceaccount:secure-ops:monitoring
   - К чему привело: rolebinding.rbac.authorization.k8s.io/escalate-binding unchanged

5. Удаление audit-policy.yaml:
   - Кто: admin
   - Возможные последствия: Удаление политики аудита уменьшает следы действий и усложняет детекцию — это явная попытка саботажа слежения.

## Вывод

### Краткая суть
Скрипт создаёт namespace/учётки, запускает тестовый «attacker» под, пытается проверить доступ сервис-аккаунта к secrets, 
создаёт привилегированный pod, читает resolv.conf у coredns, удаляет (или пытается) audit-policy, 
и в конце назначает serviceAccount monitoring роль cluster-admin. Это набор действий, типичный для сценария эскалации 
привилегий и утечки секретов.
