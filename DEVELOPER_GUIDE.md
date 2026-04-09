# Orange Canvas Node Editor - 개발자 설명서

## 개발자 가이드

이 문서는 Orange Canvas Node Editor를 확장하거나 개수정하려는 개발자를 위한 가이드입니다.

## 프로젝트 구조

```
orange_core/
├── main.py                      # 애플리케이션 진입점
├── config.py                    # 설정값 정의
├── requirements.txt             # 패키지 의존성
├── README.md                    # 프로젝트 설명
├── USER_GUIDE.md                # 사용자 가이드
├── QUICKSTART.md                # 빠른 시작 가이드
├── DEVELOPER_GUIDE.md           # 이 파일
│
└── app/
    ├── __init__.py
    ├── main_window.py           # 메인 윈도우
    │
    ├── canvas/
    │   ├── __init__.py
    │   ├── editor.py            # 캔버스 에디터 (핵심)
    │   ├── node_item.py         # 노드 시각화
    │   ├── properties.py        # 노드 속성 다이얼로그
    │
    ├── panels/
    │   ├── __init__.py
    │   ├── node_list.py         # 노드 목록 패널
    │   └── log_panel.py         # 로그 패널
    │
    ├── nodes/
    │   ├── __init__.py
    │   ├── base_node.py         # 기본 노드 클래스
    │   └── node_registry.py     # 노드 정의 및 레지스트리
    │
    └── commands/
        ├── __init__.py
        └── undo_redo.py         # Undo/Redo 시스템
```

## 핵심 모듈

### 1. base_node.py - BaseNode 클래스

```python
class BaseNode:
    """모든 노드의 기본 클래스"""
    
    def __init__(self, node_id=None, title="", image_path="", category=""):
        self.node_id = node_id              # 고유 식별자
        self.title = title                  # 노드 제목
        self.image_path = image_path        # 이미지 경로
        self.category = category            # 카테고리
        self.x, self.y = 0, 0               # 위치
        self.input_ports = {}               # 입력 포트
        self.output_ports = {}              # 출력 포트
        self.input_connections = {}         # 입력 연결
        self.output_connections = {}        # 출력 연결
    
    def add_input_port(self, name, data_type="Any"):
        """입력 포트 추가"""
    
    def add_output_port(self, name, data_type="Any"):
        """출력 포트 추가"""
```

### 2. node_registry.py - 노드 정의

노드는 이 파일에서 정의합니다:

```python
class MyCustomNode(BaseNode):
    """사용자 정의 노드"""
    
    def __init__(self, node_id=None):
        super().__init__(node_id, "My Node", "my_node.png", "Custom")
        self.add_input_port("input", "DataFrame")
        self.add_output_port("output", "DataFrame")

# 레지스트리에 등록
NODE_REGISTRY = {
    'MyCustom': MyCustomNode,
    ...
}
```

### 3. editor.py - CanvasEditor

```python
class CanvasEditor(QWidget):
    """캔버스 에디터 - 메인 작업 영역"""
    
    def add_node(self, node, x, y):
        """노드 추가"""
    
    def undo(self):
        """마지막 작업 되돌리기"""
    
    def redo(self):
        """마지막 작업 재실행"""
```

### 4. undo_redo.py - 명령 패턴

```python
class Command:
    """기본 명령 클래스"""
    
    def execute(self):
        """명령 실행"""
    
    def undo(self):
        """명령 실행 취소"""
    
    def redo(self):
        """명령 재실행"""
```

## 노드 추가 방법

### 1단계: 노드 클래스 정의

`app/nodes/node_registry.py`에서:

```python
class MyProcessingNode(BaseNode):
    """데이터 처리 노드"""
    
    def __init__(self, node_id=None):
        super().__init__(node_id, "My Processor", "processor.png", "Processing")
        
        # 입출력 포트 정의
        self.add_input_port("data", "DataFrame")
        self.add_input_port("config", "Dict")
        
        self.add_output_port("result", "DataFrame")
        self.add_output_port("stats", "Dict")
```

### 2단계: 레지스트리에 등록

같은 파일의 `NODE_REGISTRY`에:

```python
NODE_REGISTRY = {
    ...
    'MyProcessor': MyProcessingNode,
    ...
}
```

### 3단계: 카테고리 조회

```python
get_categories()  # 모든 카테고리 반환
get_nodes_by_category('Processing')  # Processing 카테고리의 노드들
```

## 명령 (Command) 추가

Undo/Redo를 지원하는 새로운 작업 추가:

```python
class MyCustomCommand(Command):
    """사용자 정의 명령"""
    
    def __init__(self, target, value):
        super().__init__(f"Custom Operation")
        self.target = target
        self.value = value
        self.old_value = None
    
    def execute(self):
        """실행"""
        self.old_value = self.target.value
        self.target.value = self.value
        logger.info(f"Applied: {self.value}")
    
    def undo(self):
        """되돌리기"""
        self.target.value = self.old_value
        logger.info(f"Undone, reverted to: {self.old_value}")
```

## 신호 (Signal) 사용

PySide6 신호를 통한 이벤트 처리:

```python
from PySide6.QtCore import Signal

class MyWidget(QWidget):
    # 신호 정의
    my_signal = Signal(str)
    another_signal = Signal(int, str)
    
    def do_something(self):
        # 신호 발출
        self.my_signal.emit("Event occurred")
        self.another_signal.emit(42, "Data")
    
    def __init__(self):
        super().__init__()
        
        # 신호 연결
        self.my_signal.connect(self.on_signal)
    
    def on_signal(self, message):
        print(f"Received: {message}")
```

## 로깅

애플리케이션 전체에서 로깅 사용:

```python
import logging

logger = logging.getLogger(__name__)

# 사용
logger.debug("Debug information")
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
```

## 파일 형식 (Canvas .canvas 파일)

Canvas 파일은 JSON 형식입니다:

```json
{
  "version": "1.0",
  "nodes": [
    {
      "node_id": 1,
      "title": "Data Source",
      "image_path": "data_source.png",
      "category": "Data",
      "x": 100,
      "y": 50,
      "input_ports": [],
      "output_ports": ["data"],
      "input_connections": {},
      "output_connections": {}
    }
  ]
}
```

## UI 커스터마이징

### 테마 변경

`config.py`에서 색상 설정:

```python
# 기존
NODE_COLOR = (100, 150, 200)

# 변경
NODE_COLOR = (200, 100, 50)  # RGB 값
```

### 노드 시각화 수정

`app/canvas/node_item.py`의 `NodeItemGraphics.paint()` 메서드:

```python
def paint(self, painter: QPainter, option, widget):
    # 배경 색상
    color = QColor(150, 200, 100)
    painter.setBrush(QBrush(color))
    painter.drawRect(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT)
    
    # 제목 그리기
    painter.setFont(QFont("Arial", 12, QFont.Bold))
    painter.drawText(10, 20, self.node.title)
```

## 이벤트 처리

### 마우스 이벤트

```python
class MyGraphicsItem(QGraphicsItem):
    def mousePressEvent(self, event):
        # 마우스 클릭
        print("Clicked!")
    
    def mouseMoveEvent(self, event):
        # 마우스 이동
        pass
    
    def mouseReleaseEvent(self, event):
        # 마우스 버튼 놓음
        pass
```

### 드래그 & 드롭

```python
def dragEnterEvent(self, event):
    if event.mimeData().hasFormat("application/x-node-type"):
        event.acceptProposedAction()

def dropEvent(self, event):
    node_type = event.mimeData().data("application/x-node-type").decode()
    # 노드 추가 처리
```

## 디버깅 팁

### 1. 로그 확인
```python
# 터미널에서 로그 확인
logger.debug(f"Current position: {self.node.x}, {self.node.y}")
```

### 2. 중단점 설정
```python
import pdb
pdb.set_trace()  # 실행 중단
```

### 3. 메모리 사용량 확인
```python
import tracemalloc
tracemalloc.start()
# ... 코드 ...
current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current}; Peak: {peak}")
```

## 성능 최적화

### 1. 노드 캐싱
```python
# 노드 인스턴스 재사용
node_cache = {}
def get_node(node_type):
    if node_type not in node_cache:
        node_cache[node_type] = create_node(node_type)
    return node_cache[node_type]
```

### 2. 배치 업데이트
```python
# 여러 업데이트를 한 번에 처리
for node in nodes:
    node.update()  # 비효율
```

```python
# 개선
scene.blockSignals(True)
for node in nodes:
    node.update()
scene.blockSignals(False)
scene.update()
```

## 테스트

단위 테스트 예제:

```python
import unittest

class TestNodeRegistry(unittest.TestCase):
    def test_node_creation(self):
        node = create_node('DataSource')
        self.assertIsNotNone(node)
        self.assertEqual(node.title, "Data Source")
    
    def test_node_ports(self):
        node = create_node('Filter')
        self.assertEqual(len(node.input_ports), 1)
        self.assertEqual(len(node.output_ports), 1)

if __name__ == '__main__':
    unittest.main()
```

## 패키징 및 배포

### EXE 파일로 변환 (Windows)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

### 소스 배포

```bash
python setup.py sdist
```

## 기여 가이드

1. Fork 하기
2. Feature branch 만들기 (`git checkout -b feature/amazing`)
3. 변경사항 Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Pull Request 만들기

## 참고 자료

- PySide6 공식 문서: https://doc.qt.io/qtforpython/
- Qt 문서: https://doc.qt.io/
- Python 로깅: https://docs.python.org/3/library/logging.html

## 라이센스

이 프로젝트는 MIT 라이센스 아래 배포됩니다.
