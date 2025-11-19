# **Expertenbericht: Beherrschung der Deterministik und sichere Deployment-Strategien für Temporal Workflows**

## **I. Zusammenfassung: Das Deterministik-Mandat und die Non-Deterministic Exception**

Die vom Benutzer beschriebene Fehlermeldung – dass der "Job während der Ausführung verändert wurde" – ist die direkte Manifestation eines Verstoßes gegen das fundamentale **Deterministik-Mandat** von Temporal. Das Verständnis dieser Kernanforderung ist entscheidend für den sicheren Betrieb verteilter, langlebiger Workflows.

### **1.1. Die Rolle der Event History Replay in der Temporal Durabilität**

Temporal gewährleistet die Ausfallsicherheit und Dauerhaftigkeit von Workflow-Ausführungen durch die vollständige Aufzeichnung aller Zustandsänderungen als unveränderliche Events in der **Event History**.1 Wenn ein Worker einen Workflow Task (Aufgabe) erhält, regeneriert er den aktuellen Workflow-Zustand, indem er diese gesamte Historie vom Anfang an "wiederabspielt" (Replay).2

Das Deterministik-Mandat erfordert, dass die Workflow-Implementierung *rein deterministisch* sein muss. Das bedeutet, dass die Wiedergabe derselben Event-Sequenz stets exakt zur gleichen Befehls-Sequenz (z. B. der Aufruf einer Activity, die Erstellung eines Timers) und dem gleichen Endzustand führen muss, unabhängig davon, welcher Worker die Wiedergabe durchführt.2

Die Einhaltung der Deterministik ist nicht nur für die Verarbeitung neuer Events wichtig, sondern auch für sekundäre Funktionen wie Abfragen (Queries) und das Zurücksetzen von Workflows.2 Eine inkorrekte Zustandsrekonstruktion während des Replay würde den gesamten Workflow blockieren und unbrauchbar machen. Bestimmte SDKs, wie das Go SDK, führen sogar Laufzeitprüfungen durch, um offensichtliche inkompatible Codeänderungen zu verhindern und sofort einen Non-Deterministischen Fehler auszulösen.3

### **1.2. Die Anatomie der NonDeterministicException**

Die NonDeterministicException tritt auf, wenn der Entwickler eine inkompatible Änderung am Workflow-Code vornimmt – beispielsweise das Hinzufügen, Entfernen oder Neuordnen von Activity-Aufrufen, Timern (workflow.NewTimer()), oder Side Effects (workflow.SideEffect()).3 Wird dieser geänderte Code auf einem Worker bereitgestellt, der versucht, eine bereits laufende Workflow-Instanz wiederzugeben (die mit dem alten Code gestartet wurde), entsteht ein kritischer Konflikt:

1. Der Worker beginnt das Replay der alten Event History.  
2. An einem bestimmten Punkt der History erwartet das SDK, basierend auf dem *alten* Code, einen bestimmten Befehl (z. B. "Activity A starten").  
3. Der *neue* Code auf dem Worker erzeugt jedoch einen *anderen* Befehl (z. B. "Activity B starten" oder gar keinen Befehl).  
4. Der Temporal Service erkennt diese Inkonsistenz zwischen dem erwarteten Befehl (aus der History) und dem vom Worker vorgeschlagenen Befehl (aus dem neuen Code).4

Dieser Konflikt führt zur NonDeterministicException. Die Folge ist, dass der Workflow-Ausführungs-Task (Workflow Task) blockiert wird. Der Temporal Service kann dem Worker nicht vertrauen, um den nächsten gültigen Zustand zu speichern, wodurch der Workflow daran gehindert wird, Fortschritte zu erzielen.4 In einem Produktionsszenario kann dieser blockierte Task wiederholt fehlschlagen, Ressourcen auf dem Worker binden und die gesamte Task Queue verlangsamen, insbesondere wenn "Tausende von Workflows" betroffen sind.5 Die unmittelbare operative Priorität liegt darin, diese blockierten Ausführungen zu identifizieren und aus dem nicht-deterministischen Loop zu befreien.

## **II. Umgang mit Non-Deterministischen Fehlern: Sofortige Sanierungsstrategien**

Die Behebung eines akuten NonDeterministicException-Falls erfordert eine gezielte Intervention, da der Fehler nicht durch herkömmliche Fehlerbehandlung im Workflow-Code selbst abgefangen werden kann.

### **2.1. Konfigurationsbasierte Fehlerbehandlung: Worker Panic Policies**

Die NonDeterministicException wird im innersten Wiederabspielmechanismus des SDKs ausgelöst, bevor die eigentliche Workflow-Logik ausgeführt wird. Daher **kann dieser Fehler nicht innerhalb des Workflow-Codes abgefangen werden**.6

Um den Workflow aus dem endlosen Workflow Task Failed-Loop zu entfernen und eine externe Sanierung zu ermöglichen, muss der Worker so konfiguriert werden, dass er bei Erkennung der Nicht-Deterministik die gesamte Workflow-Ausführung explizit fehlschlagen lässt. Dies ermöglicht es dem Betreiber, die Workflow-Instanz als *Failed* zu identifizieren und darauf zu reagieren:

* **Java/Generelle SDKs:** Durch die Verwendung von WorkflowImplementationOptions kann festgelegt werden, dass bestimmte Ausnahmen die Workflow-Ausführung fehlschlagen lassen, beispielsweise indem NonDeterministicException.class über setFailWorkflowExceptionTypes registriert wird.6  
* **Go SDK Äquivalent:** Die entsprechende Konfiguration in den WorkerOptions ist das Setzen der WorkflowPanicPolicy auf worker.FailWorkflow.6

Die erzwungene Umstellung des Workflow-Zustands von *Blocked* auf *Failed* ist ein kritischer operativer Schritt. Er ermöglicht es externen Tools und Skripten (z. B. Temporal CLI oder Visibility API), effizient alle betroffenen Ausführungen abzufragen und Listen der zu behebenden Workflows zu erstellen.5

### **2.2. Das Continue-As-New Migrationsmuster**

Sobald die Workflows in den Zustand *Failed* überführt wurden, oder um lange laufende Workflows proaktiv auf eine neue Version zu migrieren, ist der Befehl **Continue-As-New** das primäre Werkzeug.

#### **Mechanismus und Abgrenzung**

Continue-As-New ermöglicht es, den aktuellen Zustand des Workflows zu speichern und anschließend atomar eine *frische* Workflow-Ausführung zu starten. Die neue Ausführung behält dieselbe **Workflow ID**, erhält jedoch eine neue **Run ID** und beginnt mit einer vollständig geleerten Event History.1

Da die Event History zurückgesetzt wird, beginnt die neue Ausführung sauber auf der aktualisierten Codebasis, wodurch der Konflikt mit der alten, inkompatiblen History sofort behoben wird.1 Die periodische Nutzung von Continue-As-New ist generell für sehr langlebige Workflows (oft als *Entity Workflows* bezeichnet) ratsam, um sicherzustellen, dass diese nicht auf "veralteten Codeversionen" verharren und somit Versionsinkompatibilitäten bei künftigen Deployments vermieden werden.7

Es muss klar zwischen Continue-As-New und einer standardmäßigen Workflow-Wiederholung (Retry) unterschieden werden. Workflow-Retries führen die gesamte Workflow-Logik erneut aus, jedoch **gegen die bestehende Event History**.8 Wenn die Codeänderung strukturell ist, wird die Wiederholung sofort wieder den Non-Deterministik-Fehler auslösen. Continue-As-New hingegen schafft eine neue, ungebundene Ausführungsumgebung.7

Die Kombination der Worker-Policy (Fail Workflow bei Non-Deterministik) und externer Skripting-Tools ermöglicht einen automatisierten Triage-Ablauf: Identifiziere den fehlgeschlagenen Workflow $\\rightarrow$ Extrahiere die letzten bekannten Eingaben $\\rightarrow$ Löse einen Continue-As-New-Befehl mit den korrekten neuen Inputs aus $\\rightarrow$ Der Workflow wird auf dem neuen Code fortgesetzt. Dieses Muster skaliert die Sanierung auch bei einer großen Anzahl betroffener Workflows.

Die folgende Tabelle verdeutlicht die unterschiedlichen Anwendungsfälle von Workflow-Statusübergängen:

Vergleich der Workflow-Zustandsmigrations-Techniken

| Technik | Auslöser | Event History Auswirkung | Versionsmigration | Anwendungsfall |
| :---- | :---- | :---- | :---- | :---- |
| Workflow Retry | Externer Fehler/Timeout | Wiederholung gegen **existierende** History | Keine (Wiederholung des alten Ablaufs) | Transiente Fehler, behebbarer Activity-Fehler 8 |
| Continue-As-New | Interner Workflow Befehl | **Setzt History zurück**, startet sauberen Lauf | Exzellent | Code-Updates, Begrenzung der History-Größe 1 |
| Signal/Start Neu | Externer Client | Startet vollständig neue Ausführung (neue Run ID) | Exzellent | Vollständige Überarbeitung der Workflow-Logik/Totalausfall 6 |

### **2.3. Aktivitäten bei Bulk-Sanierung**

Für die Bewältigung der Herausforderung, Tausende von festsitzenden Workflows zu beheben 5, ist ein skriptgesteuerter Batch-Ansatz unerlässlich:

1. **Abfrage:** Nutzen Sie die Temporal Visibility Tools (CLI oder API), um Workflows abzufragen, die sich im Zustand Failed befinden, nachdem die Panic Policy angewendet wurde.  
2. **Batch-Aktion:** Führen Sie ein Skript aus, das die notwendigen Workflow-Parameter extrahiert und für jede identifizierte Ausführung entweder einen Continue-As-New Befehl auslöst oder, falls der Zustand vollständig verloren gehen darf, die Ausführung beendet und neu startet.

## **III. Die Strategische Kernlösung: Workflow-Versionierung beherrschen**

Die Behebung akuter Non-Deterministik-Fehler durch Neustart oder Migration ist operativ notwendig, aber die strategische Lösung zur Vermeidung dieser Probleme liegt in der korrekten Anwendung der Workflow-Versionierung. Versionierung ist die Fähigkeit, erfolgreiche Codeänderungen bereitzustellen, selbst wenn Workflow-Ausführungen, die mit dem ursprünglichen Code gestartet wurden, noch aktiv sind.4

### **3.1. Worker Versioning: Der moderne Infrastruktur-Ansatz**

Worker Versioning ist der präferierte, moderne Ansatz von Temporal, der die Kompatibilität auf die Infrastruktur- und Routing-Ebene verlagert.3

#### **3.1.1. Aufbau von Worker Deployment Versions und Build IDs**

* **Build ID:** Ein eindeutiger Tag (z. B. Semantic Version oder Commit Hash), der eine spezifische Code-Revision identifiziert.9  
* **Worker Deployment Version:** Die Kombination aus einem Deployment-Namen und der zugehörigen Build ID.9  
* **Registrierung:** Wenn ein versionierter Worker eine Task Queue (Aufgabenwarteschlange) abfragt, wird diese Task Queue Teil der Worker Version. Temporal übernimmt dann das Routing des Traffics basierend auf diesen registrierten Versionen.9

#### **3.1.2. Workflow Pinning (Pinning-Verhalten)**

Worker Versioning führt das Konzept des **Workflow Pinning** ein, welches das Verhalten von Workflows bei Versionswechseln steuert.9

* **Pinned Behavior (Gepinnte Workflows):** Eine Workflow-Ausführung, die als Pinned deklariert ist, ist garantiert, **ihre gesamte Laufzeit auf der Worker Deployment Version abzuschließen, auf der sie gestartet wurde**.9  
  * Die große architektonische Bedeutung hierbei ist, dass für diese langlebigen, gepinnten Workflows **kein manuelles Patching** mehr erforderlich ist, da sie niemals auf den neuen, inkompatiblen Codepfad gelangen.9  
* **Auto-Upgrade Behavior:** Workflows, die als Auto-Upgrade konfiguriert sind, können nach dem Deployment zu einer neueren, kompatiblen Version migriert werden.  
* **Start-Garantie:** Unabhängig vom Pinning-Verhalten beginnen Workflows nur auf der aktuell aktiven (Current) oder der hochgefahrenen (Ramping) Version des Deployments.9

Worker Versioning verlagert die Verantwortung für die Kompatibilität von der komplexen, fehleranfälligen Code-Logik auf die kontrollierte, infrastrukturseitige Verwaltung der Deployment-Versionen.

### **3.2. Legacy-Ansatz: Patching (TemporalChangeVersion)**

Patching ist die ältere Methode zur Versionskontrolle innerhalb des Workflow-Codes, die in erster Linie für das Management in-flight Workflows konzipiert ist.3

* **Anwendung:** Patching verwendet SDK-Funktionen (wie GetVersion oder die ältere TemporalChangeVersion), um bedingte Codezweige einzufügen, die an bestimmte Revisionen gebunden sind.3  
* **Funktionsweise:** Die Patch-Logik wird nur ausgeführt, wenn die Event History des Workflows die Ausführung dieses spezifischen Patch-Markers noch nicht aufgezeichnet hat. Workflows, die vor dem Deployment gestartet wurden, führen den alten Pfad innerhalb des Patch-Blocks aus. Neuere Workflows überspringen den Patch-Block und nutzen den neuen Code.  
* **Code-Management:** Patching führt zu technischer Schuld. Sobald keine aktiven Ausführungen mehr die ursprüngliche Version (z. B. version \== 2 im Beispiel) verwenden, **muss** der Patch-Block entfernt werden.3 Das Versäumnis, Patches zu entfernen, führt zu unnötig verzweigter Logik und erhöht die Wartungskomplexität.

Worker Versioning wird als die bessere, sauberere Alternative angesehen, da es das Management kompatibler Pfade auf die Infrastrukturschicht verschiebt und somit die Workflow-Definition von Kompatibilitätslogik befreit.3

## **IV. Produktions-Deployment-Strategien und Worker-Lebenszyklusmanagement**

Eine sichere Temporal-Bereitstellung erfordert moderne Deployment-Strategien, die die Steuerung des Traffics und die sichere Stilllegung alter Worker-Versionen ermöglichen.

### **4.1. Vergleich der Deployment-Modelle**

Die Auswahl der Strategie sollte auf Temporal's Worker Versioning aufbauen, um Hochverfügbarkeit und sofortige Rollbacks zu gewährleisten.9

Deployment-Strategien im Temporal-Kontext

| Strategie | Versionsmigration | Verfügbarkeit/Rollback | Worker Versioning Kompatibilität | Risikoprofil |
| :---- | :---- | :---- | :---- | :---- |
| Rolling Update (Traditionell) | Erzwingt sofortige Aktualisierung | Niedrig/langsamer Rollback | Inkompatibel | Hoch (Kontrollverlust, hohes Risiko von Non-Deterministik-Fehlern) 9 |
| Blue-Green Deployment | Gesteuerte Traffic-Verschiebung | Hoch/Sofortiger Rollback | Erforderlich | Mittel |
| Rainbow Deployment | Gepinnte Workflows werden abgebaut (Draining) | Maximierte Verfügbarkeit | Optimiert für Draining und Pinning 9 | Niedrig |

Traditionelle Rolling Deployments sind explizit als inkompatibel mit Worker Versioning gekennzeichnet 9, da sie nur eine langsame Wiederherstellung ermöglichen und nicht die notwendige Kontrolle über das Routing bieten. Die Rainbow-Strategie ist architektonisch am sichersten, da sie es erlaubt, neue Revisionen freizugeben, während ältere Versionen kontrolliert geleert werden (Draining).9

### **4.2. Deep Dive: Sunsetting und Draining von Worker-Versionen**

Der Draining-Prozess ist der operative Sicherheitsmechanismus, der die sichere Stilllegung alter Worker-Versionen ermöglicht, nachdem sie ihre Verpflichtungen gegenüber den gepinnten Workflows erfüllt haben.9

#### **4.2.1. Der Technische Prozess der Draining-Zustände**

Eine Worker Deployment Version durchläuft im Stilllegungsprozess folgende Zustände:

1. **Inactive (Inaktiv):** Die Version wurde registriert, aber noch nicht gepollt, oder sie ist nicht mehr aktiv.9  
2. **Active (Aktiv):** Die Version ist entweder die Current Version oder die Ramping Version und akzeptiert neue Workflows sowie existierende Auto-Upgrade Workflows.9  
3. **Draining (Wird geleert):** Die Version ist nicht mehr als aktuelle oder hochfahrende Version markiert, aber es laufen noch **offene gepinnte Workflows** darauf.9 Die Version wird gewartet, um diesen Workflows den Abschluss auf dem deterministischen Code zu garantieren, mit dem sie gestartet wurden.  
4. **Drained (Geleert):** Alle gepinnten Workflows, die auf dieser Version liefen, sind abgeschlossen (closed). Die Worker, die diese Version ausführen, können nun sicher außer Betrieb genommen werden.9

#### **4.2.2. Überwachung des Draining-Status**

Die operative Integrität des Worker-Sunsetting hängt von der korrekten Überwachung des Draining-Status ab.

* **Statusaktualisierung:** Der Temporal Service aktualisiert den Draining-Status periodisch, indem er die Anzahl der offenen, gepinnten Workflows zählt, die diese Version nutzen.9  
* **Sicherheitsaspekt:** Der Draining-Status wird in der WorkerDeploymentVersionStatus angezeigt und kann über die CLI (temporal worker deployment describe-version) eingesehen werden.9 Ein wichtiger technischer Aspekt ist, dass eine Version für eine kurze Zeit den Status Draining anzeigen kann, obwohl keine offenen gepinnten Workflows mehr vorhanden sind, da der Status nur **periodisch** aktualisiert wird.9  
* **Implikation für den Betrieb:** Betreiber müssen auf den definitiven Status Drained warten, bevor sie die Worker physisch herunterfahren. Die DrainageInfo.last\_checked\_time gibt Aufschluss darüber, wann die letzte Überprüfung durch den Temporal Service stattgefunden hat.9 Dies erfordert eine obligatorische Wartezeit oder eine Verifizierungsschleife in der CI/CD-Pipeline, um Race Conditions zu vermeiden, die entstehen, wenn der Worker abgeschaltet wird, bevor der Temporal Service das Ende aller gepinnten Ausführungen registriert hat. Der Zustand Draining ist somit direkt kausal für die Vermeidung der Non-Deterministik-Fehler, da er die Ausführung langlebiger Prozesse auf dem garantiert kompatiblen Code sichert.

### **4.3. Automatisierung des Versionierungs-Lebenszyklus**

Das manuelle Management von Build ID-Registrierungen, Traffic-Ramping und der Draining-Überwachung über verschiedene Worker-Deployments hinweg ist komplex. Um diesen operativen Overhead zu eliminieren, wird der Einsatz eines **Temporal Worker Controllers** empfohlen.10

Der Controller, oft in Kubernetes-Umgebungen eingesetzt, automatisiert den gesamten Worker Versioning Lifecycle 11:

* **Automatische Temporal-Integration:** Der Controller registriert Versionen und verwaltet das Routing ohne manuelle API-Aufrufe.  
* **Kubernetes-Native Workflows:** Er ermöglicht vollständige Rainbow Deployments durch die Aktualisierung einer einzelnen Custom Resource.  
* **Intelligente Bereinigung:** Er überwacht den Draining-Status und entfernt automatisch ungenutzte Ressourcen, sobald eine Version offiziell Drained ist.10

## **V. Operationelle Resilienz, Skalierung und Observability**

Über die Versionskontrolle hinaus muss die Deployment-Strategie Aspekte der Worker-Leistung, Skalierung und Überwachung umfassen, um einen stabilen Betrieb zu gewährleisten.

### **5.1. Erweiterte Worker-Leistungsoptimierung und Parallelität**

Die Leistung der Worker hängt maßgeblich von der Fähigkeit ab, die Ressourcen für unterschiedliche Aufgabentypen zu steuern.

#### **5.1.1. Task Slots und Kapazitätsmanagement**

Ein Worker Task Slot repräsentiert die Kapazität eines Temporal Workers, eine einzelne parallele Aufgabe auszuführen, sei es ein Workflow Task oder ein Activity Task.12 Die Anzahl der verfügbaren Slots definiert die maximale gleichzeitige Verarbeitungskapazität.

#### **5.1.2. Implementierung von Slot Suppliers**

Die Worker-Leistungsoptimierung verwendet **Worker Tuner**, die **Slot Suppliers** verschiedenen Aufgabentypen (Workflow, Activity, Nexus, Local Activity) zuweisen.12

* **FixedSizeSlotSupplier:** Garantiert eine feste Obergrenze der Slots. Dies ist ideal für Workflows, da Workflow Tasks oft CPU-gebunden sind (aufgrund des Replay-Mechanismus) und eine vorhersehbare, begrenzte Kapazität benötigen.13  
* **ResourceBasedSlotSupplier:** Passt die Slot-Zuweisung dynamisch basierend auf verfügbaren Ressourcen (CPU/Speicher) an. Dies ist für Activity Tasks besser geeignet, da diese oft I/O-gebunden sind und variierende Lasten verursachen.13  
* **CustomSlotSupplier:** Ermöglicht die Implementierung hochspezialisierter, benutzerdefinierter Zuweisungslogik.13

Die Verwendung unterschiedlicher Slot Suppliers für Workflow und Activity Tasks ist ein wichtiges architektonisches Detail. Es verhindert, dass ressourcenintensive Activity-Bursts die Kapazität für kritische Workflow-Replay-Aufgaben monopolisieren. Es wird darauf hingewiesen, dass die Worker Tuner die älteren Konfigurationsoptionen (maxConcurrentXXXTask) ablösen und deren gleichzeitige Verwendung zu Initialisierungsfehlern führt.12

### **5.2. Resilienz-Tuning: Timeouts und Retry Policies**

Explizit definierte Timeouts sind entscheidend, um Kontrollgrenzen für die Ausführungsdauer festzulegen.

#### **5.2.1. Activity Timeouts**

Temporal definiert vier Timeouts für Activities, von denen die folgenden die relevantesten für die Resilienz sind 15:

* **Schedule-To-Close:** Begrenzt die maximale End-to-End-Ausführungszeit der Activity, **einschließlich aller Wiederholungen**.15 Ist dieser Wert nicht gesetzt, kann er standardmäßig auf den Workflow Run Timeout (potenziell 10 Jahre) gesetzt werden.8 Dieser Standardwert ist riskant, da er zugrunde liegende, wiederkehrende Probleme maskiert.  
* **Start-To-Close:** Begrenzt die maximale Ausführungszeit einer **einzelnen Task-Ausführung**. Es wird dringend empfohlen, diesen Timeout **immer** explizit zu setzen.15  
* **Best Practice:** Die allgemeine Empfehlung ist, für Activities sehr lange ScheduleToClose-Timeouts zu definieren, um der Retry Policy maximale Flexibilität bei der Behebung intermittierender Fehler zu geben, anstatt den gesamten Workflow frühzeitig fehlschlagen zu lassen.8

#### **5.2.2. Retry Policies**

Retry Policies steuern, wie Temporal auf Fehler bei der Ausführung von Activity Tasks oder der gesamten Workflow Execution reagiert.16

* **Activity Retries:** Werden durch die ScheduleToClose-Grenze limitiert. Die Richtlinie kann maximale Versuche (withMaximumAttempts), exponentielle Backoffs oder Ausschlusslisten für bestimmte Fehler (withDoNotRetry) festlegen.17  
* **Workflow Retries:** Wenn der Workflow fehlschlägt, wird er gemäß der definierten Retry Policy bis zum WorkflowExecutionTimeout oder der maximalen Anzahl von Versuchen wiederholt.17 Im Falle eines Retries wird die gesamte Workflow-Logik von Grund auf neu ausgeführt.8 Es ist wichtig zu beachten, dass Retry Policies nicht für Workflow Task Executions gelten; diese versuchen automatisch, sich mit exponentiellem Backoff zu wiederholen, bis der Workflow Execution Timeout erreicht ist.16

### **5.3. Observability und Gesundheitsüberwachung**

Ein stabiles Deployment erfordert eine kontinuierliche Überwachung der Anwendung und der zugrundeliegenden Infrastruktur.18

* **Metrikquellen:**  
  * **Cloud/Server Metrics:** Metriken des Temporal Service selbst (Frontend, History, Matching), die die Infrastrukturleistung messen.18  
  * **SDK Metrics:** Metriken, die von den Worker-Prozessen emittiert werden und das Verhalten der Anwendung und des Codes (z. B. Slot-Nutzung, Task-Latenz, Polling-Raten) überwachen.18  
* **Implementierung:** Die Metriken können über OpenMetrics- oder PromQL-Endpunkte abgerufen und in Tools wie Prometheus und Grafana visualisiert werden.18  
* **Wichtige Überwachungsziele:** Die Überwachung der SDK-Metriken auf Ebene einzelner Worker (z. B. auf spezifischen Ports wie in dem Prometheus-Konfigurationsbeispiel gezeigt 19) liefert detaillierte Informationen über die Verteilung der Workload und die tatsächliche Slot-Auslastung.12 Dies ermöglicht eine proaktive Erkennung von Engpässen und die Optimierung der Worker-Skalierung, bevor die Task Queues überlastet werden. Darüber hinaus muss der DrainageStatus des Worker Deployments kontinuierlich überwacht werden, um den sicheren Betrieb während des Sunsetting zu gewährleisten.9

## **VI. Schlussfolgerungen und Handlungsempfehlungen**

Die NonDeterministicException ist ein deutliches Signal, dass die operative Disziplin im Umgang mit langlebigen, zustandsbehafteten Prozessen durchbrochen wurde. Die Behebung erfordert sofortige Sanierung und eine strategische Umstellung auf moderne Worker-Versionierungsmodelle.

Die Analyse führt zu folgenden kritischen Empfehlungen für eine robuste Temporal-Produktionsumgebung:

1. **Behebung akuter Fehler:** Sofortige Konfiguration der Worker-Laufzeitumgebung, um bei einer NonDeterministicException die Workflow-Ausführung explizit fehlschlagen zu lassen (z. B. WorkflowPanicPolicy: worker.FailWorkflow).6 Dies überführt blockierte Workflows in einen adressierbaren Zustand.  
2. **Migration blockierter Workflows:** Nutzung von Continue-As-New als primäres Werkzeug zur Migration inkompatibler, aktiver Workflow-Instanzen. Dadurch wird die Event History atomar zurückgesetzt, und die Ausführung kann auf dem neuen Code fortgesetzt werden.1  
3. **Strategische Versionskontrolle:** Implementierung des **Worker Versioning** mit Build IDs als Standard. Dies ersetzt das fehleranfällige und wartungsintensive In-Code-Patching für die meisten Anwendungsfälle.3  
4. **Deployment-Modell:** Einführung der **Rainbow Deployment** Strategie in Verbindung mit **Workflow Pinning**. Gepinnte Workflows garantieren, dass langlebige Ausführungen ungestört auf der Version abgeschlossen werden, auf der sie gestartet wurden.9  
5. **Sicheres Sunsetting:** Die Worker-Stilllegung muss durch die Überwachung des DrainageStatus des Temporal Service gesteuert werden. Die physische Abschaltung alter Worker-Instanzen darf erst erfolgen, nachdem der Status definitiv Drained anzeigt, um die Integrität aller gepinnten Workflows zu gewährleisten.9  
6. **Leistungs- und Resilienz-Tuning:** Verwendung von **Worker Tunern** und dezidierten Slot Suppliers (z. B. FixedSizeSlotSupplier für Workflow Tasks) zur Optimierung der Ressourcenverteilung zwischen CPU-gebundenen Workflow-Tasks und I/O-gebundenen Activity-Tasks.12  
7. **Explizite Timeouts:** Das Setzen von Start-To-Close Timeouts für Activities ist obligatorisch, um die Dauer einzelner Ausführungen zu begrenzen und unkontrollierte Laufzeiten zu verhindern.15  
8. **Automatisierung:** Bei Kubernetes-Deployments wird der Einsatz des **Temporal Worker Controllers** empfohlen, um den gesamten Versionierungs- und Draining-Lebenszyklus zu automatisieren und das höchste Maß an operationeller Sicherheit zu erreichen.10

#### **Referenzen**

1. Managing very long-running Workflows with Temporal, Zugriff am November 15, 2025, [https://temporal.io/blog/very-long-running-workflows](https://temporal.io/blog/very-long-running-workflows)  
2. Temporal Time Traveling: Replay \- Keith Tenzer, Zugriff am November 15, 2025, [https://keithtenzer.com/temporal/temporal\_time\_travelling\_replay/](https://keithtenzer.com/temporal/temporal_time_travelling_replay/)  
3. Versioning \- Go SDK | Temporal Platform Documentation, Zugriff am November 15, 2025, [https://docs.temporal.io/develop/go/versioning](https://docs.temporal.io/develop/go/versioning)  
4. Learn Temporal Workflow Versioning with free hands-on training, Zugriff am November 15, 2025, [https://temporal.io/blog/learn-temporal-workflow-versioning-with-free-hands-on-training](https://temporal.io/blog/learn-temporal-workflow-versioning-with-free-hands-on-training)  
5. How to automatically restart workflow which have non deterministic error, Zugriff am November 15, 2025, [https://community.temporal.io/t/how-to-automatically-restart-workflow-which-have-non-deterministic-error/7530](https://community.temporal.io/t/how-to-automatically-restart-workflow-which-have-non-deterministic-error/7530)  
6. Catching NonDeterministicException \- Community Support \- Temporal, Zugriff am November 15, 2025, [https://community.temporal.io/t/catching-nondeterministicexception/5020](https://community.temporal.io/t/catching-nondeterministicexception/5020)  
7. Continue-As-New | Temporal Platform Documentation, Zugriff am November 15, 2025, [https://docs.temporal.io/workflow-execution/continue-as-new](https://docs.temporal.io/workflow-execution/continue-as-new)  
8. Understanding workflow retries and failures \- Community Support \- Temporal, Zugriff am November 15, 2025, [https://community.temporal.io/t/understanding-workflow-retries-and-failures/122](https://community.temporal.io/t/understanding-workflow-retries-and-failures/122)  
9. Worker Versioning | Temporal Platform Documentation, Zugriff am November 15, 2025, [https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning](https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning)  
10. temporalio/temporal-worker-controller \- GitHub, Zugriff am November 15, 2025, [https://github.com/temporalio/temporal-worker-controller](https://github.com/temporalio/temporal-worker-controller)  
11. The Future of Friction-Free Workflow Upgrades | Replay 2024 \- YouTube, Zugriff am November 15, 2025, [https://www.youtube.com/watch?v=z2dzN5aZN\_8](https://www.youtube.com/watch?v=z2dzN5aZN_8)  
12. Worker performance | Temporal Platform Documentation, Zugriff am November 15, 2025, [https://docs.temporal.io/develop/worker-performance](https://docs.temporal.io/develop/worker-performance)  
13. temporalio.worker \- Temporal Python API Documentation, Zugriff am November 15, 2025, [https://python.temporal.io/temporalio.worker.html](https://python.temporal.io/temporalio.worker.html)  
14. SlotSupplier (temporal-sdk 1.31.0 API) \- javadoc.io, Zugriff am November 15, 2025, [https://www.javadoc.io/doc/io.temporal/temporal-sdk/latest/io/temporal/worker/tuning/SlotSupplier.html](https://www.javadoc.io/doc/io.temporal/temporal-sdk/latest/io/temporal/worker/tuning/SlotSupplier.html)  
15. Understanding the 4 types of Activity timeouts in Temporal, Zugriff am November 15, 2025, [https://temporal.io/blog/activity-timeouts](https://temporal.io/blog/activity-timeouts)  
16. What is a Temporal Retry Policy?, Zugriff am November 15, 2025, [https://docs.temporal.io/encyclopedia/retry-policies](https://docs.temporal.io/encyclopedia/retry-policies)  
17. Timeouts and retries | ZIO Temporal \- Vitalii Honta, Zugriff am November 15, 2025, [https://zio-temporal.vhonta.dev/docs/resilience/retries](https://zio-temporal.vhonta.dev/docs/resilience/retries)  
18. Temporal Cloud Observability and Metrics, Zugriff am November 15, 2025, [https://docs.temporal.io/cloud/metrics](https://docs.temporal.io/cloud/metrics)  
19. Monitor Temporal Platform metrics, Zugriff am November 15, 2025, [https://docs.temporal.io/self-hosted-guide/monitoring](https://docs.temporal.io/self-hosted-guide/monitoring)