import ezdxf
import csv
import math


# CAD 파일의 경로를 설정합니다.
dxf_path = r"XR-KY-1-ELECTODE_SF_EQUIP_ver10_1..dxf"

# 출력할 CSV 파일의 경로를 설정합니다.
csv_path = "output1.csv"

# DXF 파일을 읽어들입니다.
doc = ezdxf.readfile(dxf_path)

# 모델 스페이스를 가져옵니다.
msp = doc.modelspace()

# 노드 정보를 딕셔너리에 저장하는 함수
def collect_node_data(msp):
    node_data = {}
    for entity in msp.query('INSERT'):
        if entity.dxf.name == "Node_POINT_B_powder_plus":
            for attrib in entity.attribs:
                if attrib.dxf.tag == "NUMBER":
                    node_id = attrib.dxf.text.zfill(5)
                    position = (entity.dxf.insert.x, entity.dxf.insert.y)
                    node_data[node_id] = position
                    break
    return node_data

# 두 점 사이의 거리를 계산하는 함수
def calculate_distance(p1, p2):
    # p1과 p2는 (x, y) 형태의 좌표를 갖는 튜플입니다.
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

# 선과 호 엔티티를 순회하며 링크 정보를 수집하는 함수
def collect_links(msp, nodes):
    links = []
    for entity in msp.query('LINE ARC'):
        if entity.dxftype() == 'LINE':
            length = calculate_distance(entity.dxf.start, entity.dxf.end)
        elif entity.dxftype() == 'ARC':
            length = calculate_arc_length(entity.dxf.radius, entity.dxf.start_angle, entity.dxf.end_angle)
        else:
            continue

def get_direction_by_color(color):
    # 색상 코드에 따라 방향성을 결정합니다.
    if color == 5:  # 파란색, 양방향 링크
        return 'bidirectional'
    elif color == 1:  # 빨간색, 아래에서 위로
        return 'from_bottom_to_top'
    elif color == 3:  # 초록색, 위에서 아래로
        return 'from_top_to_bottom'
    elif color == 4:  # 하늘색, 오른쪽에서 왼쪽으로
        return 'from_right_to_left'
    elif color == 2:  # 노란색, 왼쪽에서 오른쪽으로
        return 'from_left_to_right'
    # 추가적인 색상 코드에 대한 방향성을 여기에 정의합니다.
    else:
        return 'unknown'  # 알 수 없거나 정의되지 않은 색상

        # 링크 정보 추가
        links.append({
            'color': color,
            'start': entity.dxf.start,
            'end': entity.dxf.end,
            'length': length,
            'direction': direction
        })
    return links

# 가장 가까운 노드를 찾는 함수도 튜플을 사용하도록 수정합니다.
def find_closest_node(point, nodes):
    # 가장 가까운 노드와 그 거리를 찾습니다.
    closest_node = None
    min_distance = float('inf')
    for node_id, node_position in nodes.items():
        distance = calculate_distance(point, node_position)
        if distance < min_distance:
            min_distance = distance
            closest_node = node_id
    return closest_node

# 호 길이를 계산하는 함수
def calculate_arc_length(radius, start_angle, end_angle):
    # 각도를 라디안으로 변환합니다.
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    # 호(arc)의 길이를 계산합니다.
    return radius * abs(end_rad - start_rad)

def calculate_distance(p1, p2):
    # p1과 p2는 (x, y) 형태의 튜플이어야 합니다.
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

def get_direction_by_color(color):
    # 색상 코드에 따라 방향성을 결정합니다.
    if color == 5:  # 파란색, 양방향 링크
        return 'bidirectional'
    elif color == 1:  # 빨간색, 아래에서 위로
        return 'from_bottom_to_top'
    elif color == 3:  # 초록색, 위에서 아래로
        return 'from_top_to_bottom'
    elif color == 4:  # 하늘색, 오른쪽에서 왼쪽으로
        return 'from_right_to_left'
    elif color == 2:  # 노란색, 왼쪽에서 오른쪽으로
        return 'from_left_to_right'
    else:
        return 'unknown'  # 알 수 없거나 정의되지 않은 색상

# 가장 가까운 노드를 찾는 함수
def find_closest_node(point, nodes):
    closest_node = None
    min_distance = float('inf')  # 초기 거리는 무한대로 설정
    for node_id, node_point in nodes.items():
        distance = calculate_distance(point, node_point)
        if distance < min_distance:
            min_distance = distance
            closest_node = node_id
    return closest_node

# 선과 호 엔티티를 순회하며 링크 정보를 수집하는 함수
def collect_links(msp, nodes):
    links = []
    for entity in msp.query('LINE ARC'):
        if entity.dxftype() == 'LINE':
            start_point = (entity.dxf.start.x, entity.dxf.start.y)
            end_point = (entity.dxf.end.x, entity.dxf.end.y)
            # 나머지 로직은 동일하게 유지
            # ...

        elif entity.dxftype() == 'ARC':
            start_angle_rad = math.radians(entity.dxf.start_angle)
            end_angle_rad = math.radians(entity.dxf.end_angle)

            start_point = (
                entity.dxf.center.x + math.cos(start_angle_rad) * entity.dxf.radius,
                entity.dxf.center.y + math.sin(start_angle_rad) * entity.dxf.radius
            )
            end_point = (
                entity.dxf.center.x + math.cos(end_angle_rad) * entity.dxf.radius,
                entity.dxf.center.y + math.sin(end_angle_rad) * entity.dxf.radius
            )

            from_node_id = find_closest_node(start_point, nodes)
            to_node_id = find_closest_node(end_point, nodes)
            arc_length = calculate_arc_length(entity.dxf.radius, entity.dxf.start_angle, entity.dxf.end_angle)

            direction = get_direction_by_color(entity.dxf.color)
            link_id = f'{from_node_id}_to_{to_node_id}'

            links.append({
                'link_id': link_id,
                'from_node': from_node_id,
                'to_node': to_node_id,
                'length': arc_length,  # 여기서는 직선 거리가 아니라 호의 길이를 사용합니다.
                'direction': direction
            })

    return links

# ARC 엔티티로부터 링크 패스를 생성하는 함수
def calculate_link_paths(msp, nodes):
    link_paths = []
    for arc in msp.query('ARC'):
        # ARC의 시작점과 끝점 좌표를 계산합니다.
        arc_start = (arc.dxf.center.x + math.cos(math.radians(arc.dxf.start_angle)) * arc.dxf.radius,
                     arc.dxf.center.y + math.sin(math.radians(arc.dxf.start_angle)) * arc.dxf.radius)
        arc_end = (arc.dxf.center.x + math.cos(math.radians(arc.dxf.end_angle)) * arc.dxf.radius,
                   arc.dxf.center.y + math.sin(math.radians(arc.dxf.end_angle)) * arc.dxf.radius)

        # 시작점과 끝점에 가장 가까운 노드를 찾습니다.
        start_node_id = find_closest_node(arc_start, nodes)
        end_node_id = find_closest_node(arc_end, nodes)

        # 링크 길이를 계산합니다.
        arc_length = calculate_arc_length(arc.dxf.radius, arc.dxf.start_angle, arc.dxf.end_angle)
        direct_distance = calculate_distance(arc_start, arc_end)
        total_length = arc_length + direct_distance

        # 링크 패스 ID를 생성하고 링크 패스 정보를 리스트에 추가합니다.
        link_path_id = f'{start_node_id}_to_{end_node_id}'
        link_paths.append({
            'link_path_id': link_path_id,
            'from_node': start_node_id,
            'to_node': end_node_id,
            'length': total_length
        })
    return link_paths




def write_to_csv(filename, nodes, links, link_paths):
    header = ['Node ID', 'X POS', 'Y POS', 'Link ID', 'From Node', 'To Node', 'Length', 'Link Path ID', 'From Node To Node', 'Path Length']

    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(header)  # Write the header

        for node_id, position in nodes.items():
            for link in links:
                for path in link_paths:
                    row = [node_id, position[0], position[1], link['link_id'], link['from_node'], link['to_node'], link['length'], path['link_path_id'], f"{path['from_node']}_to_{path['to_node']}", path['length']]
                    csvwriter.writerow(row)

# 기존의 노드 정보 수집 함수 호출을 수정
nodes = collect_node_data(msp)

# 링크 정보 수집
links = collect_links(msp, nodes)

# 링크패스 정보 계산
link_paths = calculate_link_paths(msp, nodes)

# CSV 파일에 데이터를 쓰는 함수 호출
write_to_csv(csv_path, nodes, links, link_paths)


