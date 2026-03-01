# Incohérences détectées dans main.py

## ❌ Erreurs critiques (bloquantes)

### 1. `state['subject_id']` non défini
- **Lignes concernées**: 248, 388, 323, 552, 615
- **Problème**: `subject_id` est utilisé dans tous les agents mais n'est pas défini dans `EEGPipelineState`
- **Solution**: Ajouter `subject_id: str` à la classe `EEGPipelineState`

### 2. `state["current_eeg_plot_url"]` non défini
- **Ligne**: 358 dans `bad_channel_identifier_agent`
- **Problème**: La variable n'existe jamais, devrait être un chemin vers une image sauvegardée
- **Solution**: Remplacer par `"./images/raw_timeseries.jpg"` (l'image est créée avant)

### 3. Syntaxe incorrecte dans `bandpass_filtering_agent_tools`
- **Ligne**: 217
- **Problème**: `type: "function"` devrait être `"type": "function"`
- **Solution**: Ajouter des guillemets autour de `type`

### 4. Mauvaise clé dans `names_to_functions`
- **Ligne**: 213
- **Problème**: `names_to_functions = {"bandpass_filtering_agent_tools": bandpass_filter}` - la clé ne correspond pas à `function_name` utilisé (qui est "bandpass_filter")
- **Solution**: Changer la clé en `"bandpass_filter"`

### 5. Double appel API redondant dans `slow_drift_analysis_agent`
- **Lignes**: 480-494
- **Problème**: Le code fait deux appels identiques à `client.chat.parse` de manière consécutive
- **Solution**: Supprimer le deuxième appel (lignes 488-494)

### 6. Mauvais accès aux résultats de l'API
- **Ligne**: 490
- **Problème**: `chat_response.slow_drift_probability` est incorrect, devrait être `result.slow_drift_probability`
- **Solution**: Utiliser `result` défini à la ligne 486

### 7. Mauvaise méthode pour afficher les composants ICA
- **Ligne**: 558
- **Problème**: `raw_ica.plot(n_components=20)` est incorrect - `raw_ica` est un objet `mne.io.Raw`, pas un objet ICA
- **Solution**: Cette partie devrait être dans `apply_ica` et utiliser `ica.plot_components()`

### 8. Accès incorrect aux résultats de parsing
- **Lignes**: 585-586
- **Problème**: `chat_response.ica_channels_to_remove` devrait être `chat_response.choices[0].message.parsed.ica_channels_to_remove`
- **Solution**: Ajouter `.choices[0].message.parsed` ou stocker d'abord le résultat dans une variable

### 9. Retour multiple non géré dans `initial_qc_agent`
- **Ligne**: 677 (dans le main)
- **Problème**: `state, SKIP_STAGE = initial_qc_agent(state)` attend 2 valeurs mais la fonction ne retourne que `state`
- **Solution**: Modifier le main pour utiliser `state = initial_qc_agent(state)` et accéder à `state['skip_stage']`

### 10. Fonction ne retourne rien
- **Ligne**: 594-598 (`apply_ica_correction`)
- **Problème**: La fonction ne retourne pas `state`
- **Solution**: Ajouter `return state` à la fin de la fonction

## ⚠️ Problèmes logiques

### 11. `bandpass_filtering_agent` ne vérifie pas si tool_calls existe
- **Ligne**: 281
- **Problème**: Peut crasher si le modèle ne retourne pas de tool_calls
- **Solution**: Ajouter une vérification `if not chat_response.choices[0].message.tool_calls:`

### 12. `notch_filtering_agent` ne fait rien quand il devrait appliquer le filtre
- **Lignes**: 437-442
- **Problème**: Dans le bloc `else`, le code dit qu'il va appliquer le filtre mais ne fait rien
- **Solution**: Implémenter l'application du filtre notch

### 13. État d'initialisation incomplet dans le main
- **Lignes**: 129-138
- **Problème**: Le state initial ne définit pas tous les champs nécessaires (manque `subject_id`, `bad_channels` initialisé, etc.)
- **Solution**: Initialiser tous les champs nécessaires

### 14. `bandpass_filtering_agent` ne retourne rien en cas d'erreur
- **Ligne**: 304
- **Problème**: En cas d'exception, la fonction n'a pas d'instruction `return`
- **Solution**: Ajouter `return state` après l'ajout de l'erreur

### 15. Initialisation de `bad_channels` manquante
- **Ligne**: 689 (dans le main)
- **Problème**: `state["bad_channels"]` est utilisé mais peut ne pas exister si `bad_channel_identifier_agent` est skippé
- **Solution**: Initialiser `bad_channels` à `[]` dans le state initial

## 📝 Problèmes de cohérence

### 16. Incohérence dans la gestion des images
- **Problème**: Certains agents génèrent et sauvegardent les images (notch_filtering_agent), d'autres supposent qu'elles existent déjà
- **Solution**: Standardiser où et quand les images sont générées

### 17. Gestion du flux `input_raw` -> `output_raw` inconsistante
- **Problème**: Certains agents copient `output_raw` vers `input_raw`, d'autres utilisent directement `input_raw`
- **Solution**: Standardiser le pattern au début de chaque agent

### 18. `ica_discrimination_agent` reçoit `raw_ica` mais devrait recevoir `ica`
- **Ligne**: 545
- **Problème**: Le paramètre `raw_ica` n'est jamais utilisé dans la fonction, devrait être l'objet ICA
- **Solution**: Modifier la signature pour recevoir l'objet `ica` et l'utiliser pour générer les plots

## 🔍 Améliorations recommandées

### 19. Validation des chemins d'images
- **Problème**: Le dossier `./images/` peut ne pas exister
- **Solution**: Créer le dossier au début du script si nécessaire

### 20. Gestion des exceptions trop générique
- **Problème**: `except Exception as e` attrape tout, rend le débogage difficile
- **Solution**: Utiliser des exceptions plus spécifiques

### 21. Chemins relatifs fragiles
- **Problème**: `"./images/*.jpg"` et `"../datasets/"` peuvent ne pas fonctionner selon le répertoire d'exécution
- **Solution**: Utiliser `Path(__file__).parent` pour des chemins relatifs au fichier

### 22. Variables d'état non typées ajoutées dynamiquement
- **Problème**: `state["slow_drift_probability"]`, `state["ica_channels_to_remove"]`, etc. ne sont pas dans `EEGPipelineState`
- **Solution**: Ajouter ces champs à TypedDict ou utiliser une structure de données plus flexible
