# Guide des Tests

## Installation des dépendances de test

```bash
pip install pytest pytest-cov pytest-mock
```

## Exécution des tests

### Exécuter tous les tests
```bash
pytest test_pipeline.py -v
```

### Exécuter des tests spécifiques
```bash
# Tester uniquement la classe TestBandpassFilter
pytest test_pipeline.py::TestBandpassFilter -v

# Tester une fonction spécifique
pytest test_pipeline.py::TestBandpassFilter::test_bandpass_filter_basic -v
```

### Exécuter avec couverture de code
```bash
pytest test_pipeline.py --cov=main --cov-report=html
```

La couverture sera générée dans `htmlcov/index.html`

### Exécuter en mode verbeux avec détails des erreurs
```bash
pytest test_pipeline.py -vv --tb=long
```

## Structure des tests

### Tests unitaires
- **TestBandpassFilter**: Tests pour le filtrage passe-bande
- **TestBadChannelHandling**: Tests pour la détection et gestion des canaux défectueux
- **TestSlowDriftCorrection**: Tests pour la correction des dérives lentes
- **TestICAProcessing**: Tests pour l'analyse en composantes indépendantes
- **TestPipelineState**: Tests pour la gestion de l'état du pipeline
- **TestDataFlow**: Tests pour le flux de données à travers le pipeline
- **TestEdgeCases**: Tests pour les cas limites et erreurs
- **TestImageDirectoryCreation**: Tests pour la gestion des répertoires
- **TestFullPipelineMock**: Tests d'intégration mockés

## Ce qui est testé

✅ Filtrage passe-bande avec différentes fréquences
✅ Annotation et interpolation des canaux défectueux  
✅ Correction des dérives lentes
✅ Application et ajustement de l'ICA
✅ Gestion de l'état du pipeline
✅ Suivi des erreurs et justifications
✅ Flux de données entre les étapes
✅ Cas limites (liste vide, tous les canaux défectueux, etc.)

## Ce qui devrait être ajouté

### Tests manquants
- Tests pour les agents avec mocking de l'API Mistral
- Tests pour la génération et sauvegarde des images
- Tests pour `notch_filtering_agent`
- Tests pour `initial_qc_agent` et `final_qc_agent`
- Tests d'intégration bout-en-bout complets
- Tests de performance

### Exemple pour mocker l'API Mistral

```python
@patch('main.client.chat.parse')
def test_slow_drift_analysis_agent(mock_chat_parse, mock_state):
    """Test slow drift analysis with mocked API"""
    # Setup mock response
    mock_result = Mock()
    mock_result.slow_drift_probability = 0.8
    mock_result.justification = "Test justification"
    
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(parsed=mock_result))]
    mock_chat_parse.return_value = mock_response
    
    # Run agent
    from main import slow_drift_analysis_agent
    result_state = slow_drift_analysis_agent(mock_state)
    
    # Assertions
    assert result_state['slow_drift_probability'] == 0.8
    assert 'slow_drift' in result_state['justification']
```

## Debugging des tests

### Afficher les prints pendant les tests
```bash
pytest test_pipeline.py -v -s
```

### Arrêter au premier échec
```bash
pytest test_pipeline.py -x
```

### Afficher les variables locales en cas d'échec
```bash
pytest test_pipeline.py --showlocals
```

## Conseils

1. **Toujours mocker les appels API externes** pour éviter les coûts et rendre les tests reproductibles
2. **Utiliser des fixtures** pour réutiliser les données de test
3. **Tester les cas limites** autant que les cas normaux
4. **Documenter les tests** pour expliquer ce qui est testé et pourquoi
5. **Maintenir une couverture > 80%** pour le code critique

## Intégration continue

Pour ajouter ces tests à une CI/CD, créez un fichier `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: pytest test_pipeline.py --cov=main
```
