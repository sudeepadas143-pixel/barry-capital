interface Props {
  hot?: number | null;
  onHover?: (desk: number | null) => void;
}

/** M1 placeholder: reserves the frame. The isometric renderer lands in M3. */
export function Scene(_props: Props) {
  return (
    <figure className="scene" aria-label="Cutaway of the office building">
      <div className="scene-frame" style={{ background: 'var(--paper-2)' }} />
      <figcaption className="scene-caption">
        <button type="button">replay arrival</button>
      </figcaption>
    </figure>
  );
}
