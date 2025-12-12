import os
import random
import time

N = 6
SHIP_SIZES = [3, 2, 1, 1]

WATER = "·"
MISS = "o"
HIT = "X"
SHIP = "■"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def inside(r, c):
    return 0 <= r < N and 0 <= c < N


def neighbors8(r, c):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if inside(rr, cc):
                yield rr, cc


def neighbors4(r, c):
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        rr, cc = r + dr, c + dc
        if inside(rr, cc):
            yield rr, cc


def print_boards(you, enemy):
    head = "   " + " ".join(str(i + 1) for i in range(N))
    print("ВАШЕ ПОЛЕ".ljust(18) + "ПОЛЕ ПРОТИВНИКА")
    print(head.ljust(18) + head)
    for r in range(N):
        left = f"{r+1:>2} " + " ".join(you[r])
        right = f"{r+1:>2} " + " ".join(enemy[r])
        print(left.ljust(18) + right)
    print()


# ---------- расстановка без касаний ----------

def can_place(cells, occupied):
    for r, c in cells:
        if (r, c) in occupied:
            return False
        for rr, cc in neighbors8(r, c):
            if (rr, cc) in occupied:
                return False
    return True


def place_ships_no_touch():
    ship_cells = []
    cell2ship = {}
    occupied = set()

    for L in SHIP_SIZES:
        tries = 0
        while True:
            tries += 1
            if tries > 5000:
                return place_ships_no_touch()

            vert = random.choice([True, False])
            if vert:
                r = random.randrange(N - L + 1)
                c = random.randrange(N)
                cells = {(r + i, c) for i in range(L)}
            else:
                r = random.randrange(N)
                c = random.randrange(N - L + 1)
                cells = {(r, c + i) for i in range(L)}

            if not can_place(cells, occupied):
                continue

            idx = len(ship_cells)
            ship_cells.append(set(cells))
            for cell in cells:
                cell2ship[cell] = idx
                occupied.add(cell)
            break

    return ship_cells, cell2ship


def ship_sunk(idx, hits, ship_cells):
    return ship_cells[idx].issubset(hits)


# ---------- ввод ----------

def read_move(used_shots):
    while True:
        s = input("Твой ход (строка столбец), например: 2 5 | exit: ").strip().lower()
        if s == "exit":
            return "EXIT"
        parts = s.split()
        if len(parts) != 2:
            continue
        if not parts[0].isdigit() or not parts[1].isdigit():
            continue
        r = int(parts[0]) - 1
        c = int(parts[1]) - 1
        if not inside(r, c):
            continue
        if (r, c) in used_shots:
            continue
        return r, c


# ---------- ИИ бота: добивание ----------

def enqueue_targets_from_hit(hit_cell, targets, bot_shots):
    r, c = hit_cell
    for rr, cc in neighbors4(r, c):
        if (rr, cc) not in bot_shots and (rr, cc) not in targets:
            targets.append((rr, cc))


def choose_bot_shot(targets, bot_shots):
    while targets:
        cell = targets.pop(0)
        if cell not in bot_shots:
            return cell
    free = [(r, c) for r in range(N) for c in range(N) if (r, c) not in bot_shots]
    return random.choice(free)


# ---------- игра ----------

def main():
    you_ships, you_c2s = place_ships_no_touch()
    bot_ships, bot_c2s = place_ships_no_touch()

    you_view = [[WATER] * N for _ in range(N)]
    for (r, c) in you_c2s:
        you_view[r][c] = SHIP

    enemy_view = [[WATER] * N for _ in range(N)]

    you_hits = set()
    bot_hits = set()
    you_shots = set()
    bot_shots = set()

    total_cells = sum(SHIP_SIZES)

    targets = []
    last_messages = []

    def redraw(extra_messages=None):
        nonlocal last_messages
        if extra_messages is not None:
            last_messages = extra_messages[:]
        clear()
        print_boards(you_view, enemy_view)
        if last_messages:
            print("\n".join(last_messages))
            print()

    redraw([])

    while True:
        if len(you_hits) == total_cells:
            redraw(["Победа! Ты уничтожил все корабли противника."])
            return
        if len(bot_hits) == total_cells:
            redraw(["Поражение. Противник уничтожил все твои корабли."])
            return

        # ====== ХОД ИГРОКА (может быть несколько раз подряд) ======
        while True:
            mv = read_move(you_shots)
            if mv == "EXIT":
                redraw(["Игра завершена досрочно."])
                return

            r, c = mv
            you_shots.add((r, c))

            msgs = []
            if (r, c) in bot_c2s:
                enemy_view[r][c] = HIT
                you_hits.add((r, c))
                idx = bot_c2s[(r, c)]
                if ship_sunk(idx, you_hits, bot_ships):
                    msgs.append("Ты ПОТОПИЛ корабль!")
                else:
                    msgs.append("Попадание! Твой ход снова.")
                redraw(msgs)

                if len(you_hits) == total_cells:
                    redraw(msgs + ["Победа! Ты уничтожил все корабли противника."])
                    return

                # попал — продолжаешь
                continue
            else:
                enemy_view[r][c] = MISS
                msgs.append("Мимо!")
                redraw(msgs)
                break  # промах — ход переходит боту

        # ====== ХОД БОТА (может быть несколько раз подряд) ======
        while True:
            time.sleep(0.6)  # задержка перед выстрелом бота

            br, bc = choose_bot_shot(targets, bot_shots)
            bot_shots.add((br, bc))

            msgs = []
            if (br, bc) in you_c2s:
                you_view[br][bc] = HIT
                bot_hits.add((br, bc))
                msgs.append(f"Противник стреляет {br+1} {bc+1}: ПОПАЛ!")
                enqueue_targets_from_hit((br, bc), targets, bot_shots)

                idx = you_c2s[(br, bc)]
                if ship_sunk(idx, bot_hits, you_ships):
                    msgs.append("Противник ПОТОПИЛ корабль!")
                    targets.clear()

                msgs.append("Противник ходит снова.")
                redraw(msgs)

                if len(bot_hits) == total_cells:
                    redraw(msgs + ["Поражение. Противник уничтожил все твои корабли."])
                    return

                # попал — стреляет ещё раз
                continue
            else:
                # промах
                if you_view[br][bc] == WATER:
                    you_view[br][bc] = MISS
                msgs.append(f"Противник стреляет {br+1} {bc+1}: мимо.")
                redraw(msgs)
                break  # промах — ход к игроку


if __name__ == "__main__":
    main()
